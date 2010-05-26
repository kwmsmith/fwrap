import os

from numpy.distutils.command.config import config as np_config, old_config
from numpy.distutils.command.build_src import build_src as np_build_src
from numpy.distutils.command.scons import scons as npscons
from Cython.Distutils import build_ext as cy_build_ext
from numpy.distutils.core import setup

def configuration(projname, extra_sources=None):
    def _configuration(parent_package='', top_path=None):
        from numpy.distutils.misc_util import Configuration
        config = Configuration(None, parent_package, top_path)

        def generate_type_config(ext, build_dir):
            config_cmd = config.get_config_cmd()
            return gen_type_map_files(config_cmd)

        def _generate_type_config(ext, build_dir):
            source = 'genconfig.f90'
            config_cmd = config.get_config_cmd()
            fh = open(source,'r')
            gc_src = fh.read()
            fh.close()
            config_cmd.try_run(body=gc_src, lang='f90')
            # add in fwrap_numpy_intp type

            return "fwrap_ktp_mod.f90"

        sources = [generate_type_config] + \
                   (extra_sources or []) + \
                   ['%s_fc.f90' % projname,
                    '%s.pyx' % projname]

        config.add_extension(projname, sources=sources)

        return config

    return _configuration

class _dummy_scons(npscons):
    def run(self):
        pass

class fw_config(np_config):
    
    def _check_compiler(self):
        old_config._check_compiler(self)
        from numpy.distutils.fcompiler import FCompiler, new_fcompiler

        if not isinstance(self.fcompiler, FCompiler):
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           dry_run=self.dry_run,
                                           force=1,
                                           requiref90=True,
                                           c_compiler=self.compiler)
            if self.fcompiler is not None:
                self.fcompiler.customize(self.distribution)
                if self.fcompiler.get_version():
                    self.fcompiler.customize_cmd(self)
                    self.fcompiler.show_customization()
                else:
                    self.warn('f90_compiler=%s is not available.' % self.fcompiler.compiler_type)
                    self.fcompiler = None

class fw_build_src(np_build_src):

    def pyrex_sources(self, sources, extension):
        cbe = cy_build_ext(self.distribution)
        cbe.finalize_options()
        return cbe.cython_sources(sources, extension)

    def f2py_sources(self, sources, extension):
        # intercept to disable calling f2py
        return sources

fwrap_cmdclass = {'config' : fw_config,
                  'build_src' : fw_build_src,
                  'scons' : _dummy_scons}
    
def gen_type_map_files(config_cmd):
    ctps = read_type_spec('fwrap_type_specs.in')
    fw2c = get_fw2c(ctps, config_cmd)
    write_f_mod('fwrap_ktp_mod.f90', fw2c)
    write_header('fwrap_ktp_header.h', fw2c)
    write_pxd('fwrap_ktp.pxd', 'fwrap_ktp_header.h', fw2c)
    return 'fwrap_ktp_mod.f90'

def read_type_spec(fname):
    from cPickle import loads
    fh = open(fname, 'r')
    ctps = loads(fh.read())
    fh.close()
    return ctps

def get_fw2c(ctps, config_cmd):
    fw2c = []
    for ctp in ctps:
        fc_type = find_fc_type(ctp['basetype'],
                    ctp['type_decl'], config_cmd)
        if not fc_type:
            raise RuntimeError(
                    "unable to find C type for type %s" % ctp['type_decl'])
        fw2c.append((ctp['fwrap_name'], fc_type))
    return fw2c

fc_type_memo = {}
def find_fc_type(base_type, decl, config_cmd):
    res = fc_type_memo.get((base_type, decl), None)
    if res is not None:
        return res
    for ctype in type_dict[base_type]:
        test_decl = '%s(kind=%s)' % (base_type, ctype)
        fsrc = fsrc_tmpl % {'TYPE_DECL' : decl,
                            'TEST_DECL' : test_decl}
        print fsrc
        if config_cmd.try_compile(body=fsrc, lang='f90'):
            res = ctype
            break
    else:
        res = ''
    fc_type_memo[base_type, decl] = res
    return res

def write_f_mod(fname, fw2c):
    f_out = open(fname, 'w')
    try:
        f_out.write('''
module fwrap_ktp_mod
    use iso_c_binding
    implicit none
''')
        for fw_name, c_type in fw2c:
            f_out.write('    integer, parameter :: %s = %s\n' % (fw_name, c_type))
        f_out.write('end module fwrap_ktp_mod\n')
    finally:
        f_out.close()

def write_header(fname, fw2c):
    h_out = open(fname, 'w')
    try:
        h_out.write("#ifndef %s\n" % fname.upper())
        h_out.write("#define %s\n" % fname.upper())
        for fw_name, fc_type in fw2c:
            c_type = f2c[fc_type]
            h_out.write('typedef %s %s;\n' % (c_type, fw_name))
        h_out.write("#endif")
    finally:
        h_out.close()

def write_pxd(fname, h_name, fw2c):
    pxd_out = open(fname, 'w')
    try:
        pxd_out.write('cdef extern from "%s":\n' % h_name)
        for fw_name, fc_type in fw2c:
            c_type = f2c[fc_type]
            pxd_out.write('    ctypedef %s %s\n' % (c_type, fw_name))
    finally:
        pxd_out.close()

fsrc_tmpl = '''
subroutine outer(a)
  use, intrinsic :: iso_c_binding
  implicit none
  %(TEST_DECL)s, intent(inout) :: a
  interface
    subroutine inner(a)
      use, intrinsic :: iso_c_binding
      implicit none
      %(TYPE_DECL)s, intent(inout) :: a
    end subroutine inner
  end interface
  call inner(a)
end subroutine outer
'''

type_dict = {
        'integer' : ('c_signed_char', 'c_short', 'c_int',
                  'c_long', 'c_long_long'),
        'real' : ('c_float', 'c_double', 'c_long_double'),
        'complex' : ('c_float_complex', 'c_double_complex', 'c_long_double_complex'),
        'character' : ('c_char',),
        }
type_dict['logical'] = type_dict['integer']

f2c = {
    'c_int'             : 'int',
    'c_short'           : 'short int',
    'c_long'            : 'long int',
    'c_long_long'       : 'long long int',
    'c_signed_char'     : 'signed char',
    'c_size_t'          : 'size_t',
    'c_int8_t'          : 'int8_t',
    'c_int16_t'         : 'int16_t',
    'c_int32_t'         : 'int32_t',
    'c_int64_t'         : 'int64_t',
    'c_int_least8_t'    : 'int_least8_t',
    'c_int_least16_t'   : 'int_least16_t',
    'c_int_least32_t'   : 'int_least32_t',
    'c_int_least64_t'   : 'int_least64_t',
    'c_int_fast8_t'     : 'int_fast8_t',
    'c_int_fast16_t'    : 'int_fast16_t',
    'c_int_fast32_t'    : 'int_fast32_t',
    'c_int_fast64_t'    : 'int_fast64_t',
    'c_intmax_t'        : 'intmax_t',
    'c_intptr_t'        : 'intptr_t',
    'c_float'           : 'float',
    'c_double'          : 'double',
    'c_long_double'     : 'long double',
    'c_float_complex'   : 'float _Complex',
    'c_double_complex'  : 'double _Complex',
    'c_long_double_complex' : 'long double _Complex',
    'c_bool'            : '_Bool',
    'c_char'            : 'char',
    }
