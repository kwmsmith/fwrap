from fwrap_src import gen_config as gc
from fwrap_src.code import CodeBuffer

from nose.tools import assert_raises

from tutils import compare

class test_genconfig(object):

    def test_gen_genconfig_main(self):
        ctps = [
            gc.ConfigTypeParam(basetype="integer",
                    ktp="kind(0)",
                    fwrap_name="fwrap_default_integer"),
            gc.ConfigTypeParam(basetype="real",
                    ktp="kind(0.0)",
                    fwrap_name="fwrap_default_real"),
            gc.ConfigTypeParam(basetype="logical",
                    ktp="kind(.true.)",
                    fwrap_name="fwrap_default_logical"),
            gc.ConfigTypeParam(basetype="complex",
                    ktp="kind((0.0,0.0))",
                    fwrap_name="fwrap_default_complex"),
             gc.ConfigTypeParam(basetype="character",
                    ktp="kind('a')",
                    fwrap_name="fwrap_default_character")
        ]
        buf = CodeBuffer()
        gc.generate_genconfig_main(ctps, buf)
        main_program = '''\
        program genconfig
            use fc_type_map
            implicit none
            integer :: iserr
            iserr = 0
            call lookup_integer(kind(0), "fwrap_default_integer", iserr)
            call lookup_real(kind(0.0), "fwrap_default_real", iserr)
            call lookup_logical(kind(.true.), "fwrap_default_logical", iserr)
            call lookup_complex(kind((0.0,0.0)), "fwrap_default_complex", iserr)
            call lookup_character(kind('a'), "fwrap_default_character", iserr)
        end program genconfig
        '''
        compare(buf.getvalue(), main_program)


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

def test_raises():
    error_spec = {
            'fwrap_foo' : 'invalid'
            }
    buf = CodeBuffer()
    assert_raises(gc.GenConfigException, gc.gen_config, error_spec, buf)
