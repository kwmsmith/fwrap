import os

from numpy.distutils.command.build_src import build_src as np_build_src
from Cython.Distutils import build_ext as cy_build_ext
from numpy.distutils.core import setup

class fw_build_src(np_build_src):

    def pyrex_sources(self, sources, extension):
        cbe = cy_build_ext(self.distribution)
        cbe.finalize_options()
        return cbe.cython_sources(sources, extension)

    def f2py_sources(self, sources, extension):
        # intercept to disable calling f2py
        return sources

fwrap_cmdclass = {'build_src' : fw_build_src}
    
def configuration(projname, extra_sources=None):
    def _configuration(parent_package='', top_path=None):
        from numpy.distutils.misc_util import Configuration
        config = Configuration(None, parent_package, top_path)

        def generate_type_config(ext, build_dir):
            source = 'genconfig.f90'
            config_cmd = config.get_config_cmd()
            fh = open(source,'r')
            gc_src = fh.read()
            fh.close()
            config_cmd.try_run(body=gc_src, lang='f90')
            # add in fwrap_numpy_intp type
            gen_type_map_files()

            return "fwrap_ktp_mod.f90"

        sources = [generate_type_config] + (extra_sources or []) + \
                ['%s_fc.f90' % projname,
                 '%s.pyx' % projname]

        config.add_extension(projname, sources=sources)

        return config

    return _configuration

def gen_type_map_files():
    fw2c = get_type_map('fwrap_type_map.out')
    write_f_mod('fwrap_ktp_mod.f90', fw2c)
    write_header('fwrap_ktp_header.h', fw2c)
    write_pxd('fwrap_ktp.pxd', 'fwrap_ktp_header.h', fw2c)

def get_type_map(map_file_name):
    fw2c = []
    map_file = open(map_file_name, 'r')
    try:
        for line in map_file.readlines():
            fw_name, c_type = line.split()
            fw2c.append((fw_name, c_type))
    finally:
        map_file.close()
    return fw2c

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

f2c = {
    'c_int' : 'int',
    'c_short' : 'short int',
    'c_long' : 'long int',
    'c_long_long' : 'long long int',
    'c_signed_char' : 'signed char',
    'c_size_t' : 'size_t',
    'c_int8_t' : 'int8_t',
    'c_int16_t' : 'int16_t',
    'c_int32_t' : 'int32_t',
    'c_int64_t' : 'int64_t',
    'c_int_least8_t' : 'int_least8_t',
    'c_int_least16_t' : 'int_least16_t',
    'c_int_least32_t' : 'int_least32_t',
    'c_int_least64_t' : 'int_least64_t',
    'c_int_fast8_t' : 'int_fast8_t',
    'c_int_fast16_t' : 'int_fast16_t',
    'c_int_fast32_t' : 'int_fast32_t',
    'c_int_fast64_t' : 'int_fast64_t',
    'c_intmax_t' : 'intmax_t',
    'c_intptr_t' : 'intptr_t',
    'c_float' : 'float',
    'c_double' : 'double',
    'c_long_double' : 'long double',
    'c_float_complex' : 'float _Complex',
    'c_double_complex' : 'double _Complex',
    'c_long_double_complex' : 'long double _Complex',
    'c_bool' : '_Bool',
    'c_char' : 'char',
    }
