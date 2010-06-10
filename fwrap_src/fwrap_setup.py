# The monkey patches, method overrides, etc. in this file are here to patch
# numpy.distutils for fwrap's purposes.

import os, sys

from numpy.distutils import exec_command as np_exec_command
orig_exec_command = np_exec_command.exec_command

def fw_exec_command( command,
                  execute_in='', use_shell=None, use_tee = None,
                  _with_python = 1,
                  **env ):
    return orig_exec_command(command,
            execute_in=execute_in,
            use_shell=use_shell,
            use_tee=0, # we override this to control output.
            _with_python=_with_python,
            **env)

np_exec_command.exec_command = fw_exec_command

from numpy.distutils import ccompiler
ccompiler.exec_command = fw_exec_command
from numpy.distutils import unixccompiler
unixccompiler.exec_command = fw_exec_command

from numpy.distutils.command.config import config as np_config, old_config
from numpy.distutils.command.build_src import build_src as np_build_src
from numpy.distutils.command.build_ext import build_ext as np_build_ext
from numpy.distutils.command.scons import scons as npscons
from Cython.Distutils import build_ext as cy_build_ext
from numpy.distutils.core import setup as np_setup

def setup(log='fwrap_setup.log', *args, **kwargs):
    if log:
        _old_stdout, _old_stderr = sys.stdout, sys.stderr
        log = open(log, 'w')
        sys.stdout = log
        sys.stderr = log
    try:
        np_setup(*args, **kwargs)
    finally:
        if log:
            log.flush()
            log.close()
            sys.stdout, sys.stderr = _old_stdout, _old_stderr

def configuration(projname, extra_sources=None):
    def _configuration(parent_package='', top_path=None):
        from numpy.distutils.misc_util import Configuration
        config = Configuration(None, parent_package, top_path)

        def generate_type_config(ext, build_dir):
            config_cmd = config.get_config_cmd()
            return gen_type_map_files(config_cmd)

        sources = [generate_type_config] + \
                   (extra_sources or []) + \
                   ['%s_fc.f90' % projname,
                    '%s.pyx' % projname]

        config.add_extension(projname, sources=sources)

        return config

    return _configuration

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
        h_out.write("#ifndef %s\n" % fname.upper().replace('.','_'))
        h_out.write("#define %s\n" % fname.upper().replace('.', '_'))
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

class fw_build_ext(np_build_ext):

    def build_extension(self, ext):
        from numpy.distutils.command.build_ext import (is_sequence,
                newer_group, log, filter_sources, get_numpy_include_dirs)
        sources = ext.sources
        if sources is None or not is_sequence(sources):
            raise DistutilsSetupError(
                ("in 'ext_modules' option (extension '%s'), " +
                 "'sources' must be present and must be " +
                 "a list of source filenames") % ext.name)
        sources = list(sources)

        if not sources:
            return

        fullname = self.get_ext_fullname(ext.name)
        if self.inplace:
            modpath = fullname.split('.')
            package = '.'.join(modpath[0:-1])
            base = modpath[-1]
            build_py = self.get_finalized_command('build_py')
            package_dir = build_py.get_package_dir(package)
            ext_filename = os.path.join(package_dir,
                                        self.get_ext_filename(base))
        else:
            ext_filename = os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname))
        depends = sources + ext.depends

        if not (self.force or newer_group(depends, ext_filename, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return
        else:
            log.info("building '%s' extension", ext.name)

        extra_args = ext.extra_compile_args or []
        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        c_sources, cxx_sources, f_sources, fmodule_sources = \
                   filter_sources(ext.sources)



        if self.compiler.compiler_type=='msvc':
            if cxx_sources:
                # Needed to compile kiva.agg._agg extension.
                extra_args.append('/Zm1000')
            # this hack works around the msvc compiler attributes
            # problem, msvc uses its own convention :(
            c_sources += cxx_sources
            cxx_sources = []

        # Set Fortran/C++ compilers for compilation and linking.
        if ext.language=='f90':
            fcompiler = self._f90_compiler
        elif ext.language=='f77':
            fcompiler = self._f77_compiler
        else: # in case ext.language is c++, for instance
            fcompiler = self._f90_compiler or self._f77_compiler
        cxx_compiler = self._cxx_compiler

        # check for the availability of required compilers
        if cxx_sources and cxx_compiler is None:
            raise DistutilsError, "extension %r has C++ sources" \
                  "but no C++ compiler found" % (ext.name)
        if (f_sources or fmodule_sources) and fcompiler is None:
            raise DistutilsError, "extension %r has Fortran sources " \
                  "but no Fortran compiler found" % (ext.name)
        if ext.language in ['f77','f90'] and fcompiler is None:
            self.warn("extension %r has Fortran libraries " \
                  "but no Fortran linker found, using default linker" % (ext.name))
        if ext.language=='c++' and cxx_compiler is None:
            self.warn("extension %r has C++ libraries " \
                  "but no C++ linker found, using default linker" % (ext.name))

        kws = {'depends':ext.depends}
        output_dir = self.build_temp

        include_dirs = ext.include_dirs + get_numpy_include_dirs()

        c_objects = []
        if c_sources:
            log.info("compiling C sources")
            c_objects = self.compiler.compile(c_sources,
                                              output_dir=output_dir,
                                              macros=macros,
                                              include_dirs=include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)

        if cxx_sources:
            log.info("compiling C++ sources")
            c_objects += cxx_compiler.compile(cxx_sources,
                                              output_dir=output_dir,
                                              macros=macros,
                                              include_dirs=include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)

        extra_postargs = []
        f_objects = []
        if fmodule_sources:
            log.info("compiling Fortran 90 module sources")
            module_dirs = ext.module_dirs[:]
            module_build_dir = os.path.join(
                self.build_temp,os.path.dirname(
                    self.get_ext_filename(fullname)))

            self.mkpath(module_build_dir)
            if fcompiler.module_dir_switch is None:
                existing_modules = glob('*.mod')
            extra_postargs += fcompiler.module_options(
                module_dirs,module_build_dir)
            f_objects += fcompiler.compile(fmodule_sources,
                                           output_dir=self.build_temp,
                                           macros=macros,
                                           include_dirs=include_dirs,
                                           debug=self.debug,
                                           extra_postargs=extra_postargs,
                                           depends=ext.depends)

            if fcompiler.module_dir_switch is None:
                for f in glob('*.mod'):
                    if f in existing_modules:
                        continue
                    t = os.path.join(module_build_dir, f)
                    if os.path.abspath(f)==os.path.abspath(t):
                        continue
                    if os.path.isfile(t):
                        os.remove(t)
                    try:
                        self.move_file(f, module_build_dir)
                    except DistutilsFileError:
                        log.warn('failed to move %r to %r' %
                                 (f, module_build_dir))
        if f_sources:
            log.info("compiling Fortran sources")
            f_objects += fcompiler.compile(f_sources,
                                           output_dir=self.build_temp,
                                           macros=macros,
                                           include_dirs=include_dirs,
                                           debug=self.debug,
                                           extra_postargs=extra_postargs,
                                           depends=ext.depends)

        objects = c_objects + f_objects

        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []
        libraries = self.get_libraries(ext)[:]
        library_dirs = ext.library_dirs[:]

        linker = self.compiler.link_shared_object
        # Always use system linker when using MSVC compiler.
        if self.compiler.compiler_type=='msvc':
            # expand libraries with fcompiler libraries as we are
            # not using fcompiler linker
            self._libs_with_msvc_and_fortran(fcompiler, libraries, library_dirs)

        # elif ext.language in ['f77','f90'] and fcompiler is not None:
            # linker = fcompiler.link_shared_object
        if ext.language=='c++' and cxx_compiler is not None:
            linker = cxx_compiler.link_shared_object

        if sys.version[:3]>='2.3':
            kws = {'target_lang':ext.language}
        else:
            kws = {}

        linker(objects, ext_filename,
               libraries=libraries,
               library_dirs=library_dirs,
               runtime_library_dirs=ext.runtime_library_dirs,
               extra_postargs=extra_args,
               export_symbols=self.get_export_symbols(ext),
               debug=self.debug,
               build_temp=self.build_temp,**kws)

class fw_build_src(np_build_src):

    def pyrex_sources(self, sources, extension):
        cbe = cy_build_ext(self.distribution)
        cbe.finalize_options()
        return cbe.cython_sources(sources, extension)

    def f2py_sources(self, sources, extension):
        # intercept to disable calling f2py
        return sources

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

class _dummy_scons(npscons):
    def run(self):
        pass

fwrap_cmdclass = {'config' : fw_config,
                  'build_src' : fw_build_src,
                  'build_ext' : fw_build_ext,
                  'scons' : _dummy_scons}
