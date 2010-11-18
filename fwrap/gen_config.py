#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from cStringIO import StringIO
from cPickle import dumps
import constants

INDENT = "    "

#------------------------------------------------------------------------------
# -- Collect, store and load type specifications to / from a file ---

def all_dtypes(ast):
    dtypes = set()
    for proc in ast:
        dtypes.update(proc.all_dtypes())
    return list(dtypes)

def extract_ctps(ast):
    return ctps_from_dtypes(all_dtypes(ast))

def ctp_from_dtype(dtype):
    return ConfigTypeParam(basetype=dtype.type,
                           fwrap_name=dtype.fw_ktp,
                           odecl=dtype.odecl,
                           npy_enum=dtype.npy_enum,
                           lang=dtype.lang)

def ctps_from_dtypes(dtypes):
    return [ctp_from_dtype(dtype)
            for dtype in dtypes
            if dtype.odecl is not None]

def generate_type_specs(ast, buf):
    ctps = extract_ctps(ast)
    _generate_type_specs(ctps, buf)

def _generate_type_specs(ctps, buf):
    out_lst = []
    for ctp in ctps:
        out_lst.append(dict(basetype=ctp.basetype,
                            odecl=ctp.odecl,
                            fwrap_name=ctp.fwrap_name,
                            npy_enum=ctp.npy_enum,
                            lang=ctp.lang))
    buf.write(dumps(out_lst))

def read_type_spec(fname):
    from cPickle import loads
    fh = open(fname, 'rb')
    ds = loads(fh.read())
    fh.close()
    return [ConfigTypeParam(**d) for d in ds]

#------------------------------------------------------------------------------
# -- Write out the type information to a Fortran module, a C header and a
#    cython .pxd

def write_f_mod(ctps, fbuf):

    def write_err_codes(f_out):
        for line in constants.get_fortran_constants_utility_code():
            f_out.write(INDENT + line + '\n')

    buf = StringIO()
    buf.write('''
module fwrap_ktp_mod
    use iso_c_binding
    implicit none
''')
    write_err_codes(buf)
    for ctp in ctps:
        for line in ctp.gen_f_mod():
            buf.write(INDENT+'%s\n' % line)
    buf.write('end module fwrap_ktp_mod\n')

    fbuf.write(buf.getvalue())

def get_c_preambles(ctps):
    blocks = set()
    for tp in ctps:
        blocks.update(tp.get_c_preambles())
    return blocks

def get_pxd_cimports(ctps):
    blocks = set()
    for tp in ctps:
        blocks.update(tp.get_pxd_cimports())
    return blocks

def write_header(ctps, fbuf):

    def write_err_codes(h_out):
        for err_name in sorted(constants.ERR_CODES):
            h_out.write("#define %s %d\n" % \
                    (err_name, constants.ERR_CODES[err_name]))

    buf = StringIO()
    buf.write("#ifndef %s\n" % fbuf.name.upper().replace('.','_'))
    buf.write("#define %s\n" % fbuf.name.upper().replace('.', '_'))
    buf.write(complex_utility_code)
    write_err_codes(buf)
    for incl in get_c_preambles(ctps):
        if incl: buf.write(incl+'\n')
    for ctp in ctps:
        for line in ctp.gen_c_typedef():
            buf.write(line+'\n')

    buf.write("#endif")

    fbuf.write(buf.getvalue())

def write_pxi(ctps, fbuf):
    
    buf = StringIO()

    buf.write("import numpy as np\n")

    for ctp in ctps:
        for line in ctp.gen_pyx_type_obj():
            buf.write(line+'\n')
    fbuf.write(buf.getvalue())

def write_pxd(ctps, fbuf, h_name):

    def write_err_codes(pxd_out):
        pxd_out.write(INDENT+"enum:\n")
        for err_name in sorted(constants.ERR_CODES):
            pxd_out.write((INDENT*2)+"%s = %d\n" %\
                    (err_name, constants.ERR_CODES[err_name]))

    buf = StringIO()
    extern_block = StringIO()
    for cimp in get_pxd_cimports(ctps):
        if cimp: buf.write(cimp+'\n')
    for ctp in ctps:
        for line in ctp.gen_pxd_intern_typedef():
            buf.write(line+'\n')
    for ctp in ctps:
        for line in ctp.gen_pxd_extern_typedef():
            extern_block.write(INDENT+line+'\n')
    for ctp in ctps:
        for line in ctp.gen_pxd_extern_extra():
            extern_block.write(INDENT+line+'\n')
    extern_block = extern_block.getvalue()
    if extern_block.rstrip():
        buf.write('cdef extern from "%s":\n' % h_name)
        write_err_codes(buf)
        buf.write(extern_block)

    fbuf.write(buf.getvalue())

#------------------------------------------------------------------------------
# -- Factory function; creates _ConfigTypeParam instances. --

def ConfigTypeParam(basetype, odecl, fwrap_name, npy_enum, lang='fortran'):
    if lang == 'c':
        return _CConfigTypeParam(basetype, odecl, fwrap_name, npy_enum)
    elif lang == 'fortran':
        if basetype == 'complex':
            return _CmplxTypeParam(basetype, odecl, fwrap_name, npy_enum)
        if basetype == 'character':
            return _CharTypeParam(basetype, odecl, fwrap_name, npy_enum)
        if basetype == 'logical':
            return _LogicalTypeParam(basetype, odecl, fwrap_name, npy_enum)
        else:
            return _ConfigTypeParam(basetype, odecl, fwrap_name, npy_enum)
    else:
        raise ValueError(
                "unknown language '%s' not one of 'c' or 'fortran'" % lang)


def py_type_name_from_type(name):
    suffix = "_t"
    if name.endswith(suffix):
        return name[:-len(suffix)]
    else:
        return "%s_" % name

class _ConfigTypeParam(object):

    lang = 'fortran'

    c_preambles = []
    pxd_cimports = []

    def __init__(self, basetype, odecl, fwrap_name, npy_enum):
        self.basetype = basetype
        self.odecl = odecl
        self.fwrap_name = fwrap_name
        self.npy_enum = npy_enum
        self.fc_type = None

    def __eq__(self, other):
        return self.basetype == other.basetype and \
                self.odecl == other.odecl and \
                self.fwrap_name == other.fwrap_name

    def get_c_preambles(self):
        if 'npy' in self.fc_type:
            return ['#include <numpy/npy_math.h>'] + self.c_preambles
        else:
            return self.c_preambles

    def get_pxd_cimports(self):
        if ('npy' in self.fc_type or
            (self.lang == 'c' and 'npy' in self.odecl)):
            return ['cimport numpy as np'] + self.pxd_cimports
        else:
            return self.pxd_cimports

    def cy_name(self):
        return self.fwrap_name

    def check_init(self):
        if self.fc_type is None:
            raise RuntimeError("fc_type is None, unable to "
                               "generate fortran type information.")

    def gen_f_mod(self):
        self.check_init()
        return ['integer, parameter :: %s = %s' %
                (self.fwrap_name, self.fc_type)]

    def gen_c_typedef(self):
        self.check_init()
        if self.lang == 'c':
            # In particular, npy_intp
            return ['typedef %s %s;' % (self.odecl, self.fwrap_name)]
        else:
            return ['typedef %s %s;' % (f2c[self.fc_type], self.fwrap_name)]

    def gen_pxd_extern_extra(self):
        return []

    def gen_pxd_extern_typedef(self):
        self.check_init()
        if self.lang == 'c':
            decl = self.odecl
            if decl.startswith('npy'):
                decl = 'np.' + decl
            return ['ctypedef %s %s' % (decl, self.fwrap_name)]
        else:
            return ['ctypedef %s %s' % (f2cy[self.fc_type], self.fwrap_name)]

    def gen_pyx_type_obj(self):
        self.check_init()
        enum_code = ['%s = np.%s' % (self.npy_enum, type2enum[self.fc_type])]
        type_obj_code = ['%s = np.%s' %
                (py_type_name_from_type(self.fwrap_name),
                 f2npy_type[self.fc_type])]
        return enum_code + type_obj_code

    def gen_pxd_intern_typedef(self):
        return []

def _get_cy_version():
    from Cython.Compiler.Version import version
    major, minor = version.split('.')[:2]
    return (int(major), int(minor))

def _get_py_version():
    import sys
    major, minor = sys.version_info[:2]
    return major, minor

def _get_pybytes():
    major, minor = _get_py_version()
    if major < 3:
        return '''\
from python_string cimport PyString_FromStringAndSize as PyBytes_FromStringAndSize
ctypedef str fw_bytes'''
    elif major == 3:
        return '''\
from python_bytes cimport PyBytes_FromStringAndSize
ctypedef bytes fw_bytes'''

class _CharTypeParam(_ConfigTypeParam):

    pxd_cimports = [_get_pybytes()]

    def _get_odecl(self):
        return "character(1)"

    def _set_odecl(self, od):
        pass

    odecl = property(_get_odecl, _set_odecl)

class _LogicalTypeParam(_ConfigTypeParam):

    def gen_f_mod(self):
        self.check_init()
        temp_var_name = "%s_tmp_var" % (self.fwrap_name)
        temp_var = "%s :: %s" % (self.odecl, temp_var_name)
        return [temp_var,
                ("integer, parameter :: %s = kind(%s)" %
                    (self.fwrap_name, temp_var_name))]

class _CmplxTypeParam(_ConfigTypeParam):

    c_includes = ['#include <complex.h>']

    _c2r_map = {'c_float_complex' : 'c_float',
                'c_double_complex' : 'c_double',
                'c_long_double_complex' : 'c_long_double',
                'npy_complex64' : 'np.float32',
                'npy_complex128' : 'np.float64',
               }

    _c2cy_map = {'c_float_complex' : 'float complex',
                 'c_double_complex' : 'double complex',
                 'c_long_double_complex' : 'long double complex',
                 'npy_complex64' : 'np.complex64',
                 'npy_complex128' : 'np.complex128'
                }

    def gen_pxd_intern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' %
                (self._c2cy_map[self.fc_type], self.fwrap_name)]

    def _cy_name(self):
        return "cy_%s" % self.fwrap_name

    def gen_pxd_extern_typedef(self):
        self.check_init()
        return []


class _CConfigTypeParam(_ConfigTypeParam):

    lang = 'c'

#------------------------------------------------------------------------------
# -- Type mapping info. --

f2c = {
    'c_int'             : 'int',
    'c_short'           : 'short int',
    'c_long'            : 'long int',
    'c_long_long'       : 'fw_long_long',
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
    'c_float_complex'   : 'fw_complex(float)',
    'c_double_complex'  : 'fw_complex(double)',
    'c_long_double_complex' : 'fw_complex(long double)',
    'c_bool'            : '_Bool',
    'c_char'            : 'char'
    }

f2cy = dict(f2c) # make copy

# Add NumPy types (used in f77binding mode)
for x in ('npy_int8', 'npy_int16', 'npy_int32', 'npy_int64',
          'npy_float32', 'npy_float64', 'npy_complex64', 'npy_complex128'):
    f2c[x] = x
    f2cy[x] = '%s_t' % x.replace('y_', '.') # npy_float64 -> np.float64_t

c2f = dict([(y,x) for (x,y) in f2c.items()])

type_dict = {
        'integer' : ('c_signed_char', 'c_short', 'c_int',
                  'c_long', 'c_long_long'),
        'real' : ('c_float', 'c_double', 'c_long_double'),
        'complex' : ('c_float_complex',
                     'c_double_complex',
                     'c_long_double_complex'),
        'character' : ('c_char',),
        }

f2npy_type = {
    'c_int'             : 'intc',
    'c_short'           : 'short',
    'c_long'            : 'int_',
    'c_long_long'       : 'longlong',
    'c_signed_char'     : 'byte',
    # 'c_size_t'          : 'size_t',
    'c_int8_t'          : 'int8',
    'c_int16_t'         : 'int16',
    'c_int32_t'         : 'int32',
    'c_int64_t'         : 'int64',
    # 'c_int_least8_t'    : 'int_least8_t',
    # 'c_int_least16_t'   : 'int_least16_t',
    # 'c_int_least32_t'   : 'int_least32_t',
    # 'c_int_least64_t'   : 'int_least64_t',
    # 'c_int_fast8_t'     : 'int_fast8_t',
    # 'c_int_fast16_t'    : 'int_fast16_t',
    # 'c_int_fast32_t'    : 'int_fast32_t',
    # 'c_int_fast64_t'    : 'int_fast64_t',
    # 'c_intmax_t'        : 'intmax_t',
    'c_intptr_t'        : 'intp',
    'c_float'           : 'single',
    'c_double'          : 'double',
    'c_long_double'     : 'longdouble',
    'c_float_complex'   : 'csingle',
    'c_double_complex'  : 'cdouble',
    'c_long_double_complex' : 'clongdouble',
    # 'c_bool'            : '_Bool',
    'c_char'            : 'byte',

    'npy_int8'          : 'int8',
    'npy_int16'         : 'int16',
    'npy_int32'         : 'int32',
    'npy_int64'         : 'int64',
    'npy_float32'       : 'float32',
    'npy_float64'       : 'float64',
    'npy_complex64'     : 'complex64',
    'npy_complex128'    : 'complex128',

    }

type2enum = {
    'c_int'             : 'NPY_INT',
    'c_short'           : 'NPY_SHORT',
    'c_long'            : 'NPY_LONG',
    'c_long_long'       : 'NPY_LONGLONG',
    'c_signed_char'     : 'NPY_BYTE',
    'c_int8_t'          : 'NPY_INT8',
    'c_int16_t'         : 'NPY_INT16',
    'c_int32_t'         : 'NPY_INT32',
    'c_int64_t'         : 'NPY_INT64',
    'c_float'           : 'NPY_FLOAT',
    'c_double'          : 'NPY_DOUBLE',
    'c_long_double'     : 'NPY_LONGDOUBLE',
    'c_float_complex'   : 'NPY_CFLOAT',
    'c_double_complex'  : 'NPY_CDOUBLE',
    'c_long_double_complex' : 'NPY_CLONGDOUBLE',
    'c_char'            : 'NPY_BYTE',

    # 'c_bool'            : '_Bool',
    # 'c_size_t'          : 'size_t',
    # 'c_int_least8_t'    : 'int_least8_t',
    # 'c_int_least16_t'   : 'int_least16_t',
    # 'c_int_least32_t'   : 'int_least32_t',
    # 'c_int_least64_t'   : 'int_least64_t',
    # 'c_int_fast8_t'     : 'int_fast8_t',
    # 'c_int_fast16_t'    : 'int_fast16_t',
    # 'c_int_fast32_t'    : 'int_fast32_t',
    # 'c_int_fast64_t'    : 'int_fast64_t',
    # 'c_intmax_t'        : 'intmax_t',
    # 'c_intptr_t'        : 'intp',

    'npy_int8'          : 'NPY_INT8',
    'npy_int16'         : 'NPY_INT16',
    'npy_int32'         : 'NPY_INT32',
    'npy_int64'         : 'NPY_INT64',
    'npy_float32'       : 'NPY_FLOAT32',
    'npy_float64'       : 'NPY_FLOAT64',
    'npy_complex64'     : 'NPY_COMPLEX64',
    'npy_complex128'    : 'NPY_COMPLEX128',
    }

complex_utility_code = """\
#if defined(__cplusplus)
   #include <complex>
   #define fw_complex(x) std::complex<x>
#else
   #define fw_complex(x) x _Complex
#endif
"""
