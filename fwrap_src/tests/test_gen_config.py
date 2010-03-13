from fwrap_src import gen_config as gc
from fwrap_src.code import CodeBuffer

from tutils import compare

def test_gen_default_int():
    dint_spec = {'fwrap_default_integer' : 'c_int' }
    buf = CodeBuffer()
    gc.gen_config(dint_spec, buf)
    output = '''\
    module config
        use iso_c_binding
        implicit none
        integer, parameter :: fwrap_default_integer = c_int
    end module config
'''
    compare(output, buf.getvalue())

def test_gen_many():
    spec = {
            'fwrap_default_double_precision' : 'c_double',
            'fwrap_default_integer' : 'c_int',
            'fwrap_default_real'    : 'c_float',
            'fwrap_foo' : 'c_short' 
            }
    buf = CodeBuffer()
    gc.gen_config(spec, buf)
    output = '''\
    module config
        use iso_c_binding
        implicit none
        integer, parameter :: fwrap_default_double_precision = c_double
        integer, parameter :: fwrap_default_integer = c_int
        integer, parameter :: fwrap_default_real = c_float
        integer, parameter :: fwrap_foo = c_short
    end module config
'''
    compare(output, buf.getvalue())
