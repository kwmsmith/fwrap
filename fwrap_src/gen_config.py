from cPickle import dumps
from fwrap_src import pyf_iface
import constants

NON_ERR_LABEL = 200
ERR_LABEL = 100

def generate_type_specs(ast, buf):
    ctps = extract_ctps(ast)
    _generate_type_specs(ctps, buf)

def _generate_type_specs(ctps, buf):
    out_lst = []
    for ctp in ctps:
        out_lst.append(dict(basetype=ctp.basetype,
                            odecl=ctp.odecl,
                            fwrap_name=ctp.fwrap_name))
    buf.write(dumps(out_lst))

def extract_ctps(ast):
    dtypes = set()
    for proc in ast:
        dtypes.update(proc.all_dtypes())
    dtypes = list(dtypes)
    return ctps_from_dtypes(dtypes)

def ctps_from_dtypes(dtypes):
    ret = []
    for dtype in dtypes:
        if dtype.odecl is None:
            continue
        ret.append(ConfigTypeParam(basetype=dtype.type,
                       fwrap_name=dtype.fw_ktp,
                       odecl=dtype.odecl))
    return ret

def ConfigTypeParam(basetype, odecl, fwrap_name):
    if basetype == 'complex':
        return _CmplxTypeParam(basetype, odecl, fwrap_name)
    else:
        return _ConfigTypeParam(basetype, odecl, fwrap_name)

class _ConfigTypeParam(object):

    def __init__(self, basetype, odecl, fwrap_name):
        self.basetype = basetype
        self.odecl = odecl
        self.fwrap_name = fwrap_name
        self.c_type = None

    def __eq__(self, other):
        return self.basetype == other.basetype and \
                self.odecl == other.odecl and \
                self.fwrap_name == other.fwrap_name

    def cy_name(self):
        return self.fwrap_name

    def check_init(self):
        if self.c_type is None:
            raise RuntimeError("c_type is None, unable to "
                               "generate fortran type information.")

    def gen_f_mod(self):
        self.check_init()
        return ['integer, parameter :: %s = %s' % (self.fwrap_name, self.c_type)]

    def gen_c_extra(self):
        return []

    def gen_c_includes(self):
        return []

    def gen_c_typedef(self):
        self.check_init()
        return ['typedef %s %s;' % (f2c[self.c_type], self.fwrap_name)]

    def gen_pxd_extern_extra(self):
        return []

    def gen_pxd_extern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' % (f2c[self.c_type], self.fwrap_name)]

    def gen_pxd_intern_typedef(self):
        return []

class _CmplxTypeParam(_ConfigTypeParam):

    _c2r_map = {'c_float_complex' : 'c_float',
               'c_double_complex' : 'c_double',
               'c_long_double_complex' : 'c_long_double'
               }

    _c2cy_map = {'c_float_complex' : 'float complex',
                 'c_double_complex' : 'double complex',
                 'c_long_double_complex' : 'long double complex'
                }
    
    def gen_c_includes(self):
        return ['#include <complex.h>']

    def gen_c_extra(self):
        self.check_init()
        return ["""\
#define %(ktp)s_creal(x) (creal(x))
#define %(ktp)s_cimag(x) (cimag(x))
#define CyComplex2%(ktp)s(x, y) (y = (__Pyx_CREAL(x) + _Complex_I * __Pyx_CIMAG(x)))
#define %(ktp)s2CyComplex(y, x) __Pyx_SET_CREAL(x, fwrap_default_complex_creal(y)); \
                           __Pyx_SET_CIMAG(x, fwrap_default_complex_cimag(y))
""" % {'ktp' : self.fwrap_name}]

    def gen_pxd_extern_extra(self):
        ctype = f2c[self._c2r_map[self.c_type]]
        fktp = self.fwrap_name
        cyktp = self.cy_name()
        d = {'fktp' : fktp,
             'cyktp' : cyktp,
             'ctype' : ctype}
        return ('%(ctype)s %(fktp)s_creal(%(fktp)s fdc)\n'
                 '%(ctype)s %(fktp)s_cimag(%(fktp)s fdc)\n'
                 'void CyComplex2%(fktp)s(%(cyktp)s cy, %(fktp)s fc)\n'
                 'void %(fktp)s2CyComplex(%(fktp)s fc, %(cyktp)s cy)\n' % d).splitlines()

    def gen_pxd_extern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' % (f2c[self._c2r_map[self.c_type]], self.fwrap_name)]

    def gen_pxd_intern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' % (self._c2cy_map[self.c_type], self.cy_name())]

    def cy_name(self):
        return "cy_%s" % self.fwrap_name

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

type_dict = {
        'integer' : ('c_signed_char', 'c_short', 'c_int',
                  'c_long', 'c_long_long'),
        'real' : ('c_float', 'c_double', 'c_long_double'),
        'complex' : ('c_float_complex', 'c_double_complex', 'c_long_double_complex'),
        'character' : ('c_char',),
        }
type_dict['logical'] = type_dict['integer']
