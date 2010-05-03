from fwrap_src import pyf_iface
from fwrap_src import gen_config as gc
from fwrap_src.code import CodeBuffer

from nose.tools import assert_raises, ok_, eq_

from tutils import compare

class test_genconfig(object):

    def test_get_ctp_list(self):
        dtypes = pyf_iface.Dtype.all_dtypes()
        ok_(dtypes)
        ctps = gc.ConfigTypeParam.from_dtypes(dtypes)
        ok_(set(map(lambda x: x.fwrap_name, ctps))
                >
                set(["fwrap_default_integer",
                        "fwrap_default_real",
                        "fwrap_default_logical",
                        "fwrap_default_double",
                        "fwrap_default_complex",
                        "fwrap_default_double_complex",
                        ]))
        ok_(set(map(lambda x: x.ktp, ctps))
                >
                set(["kind(0)",
                        "kind(0.0)",
                        "kind(0.0D0)",
                        "kind((0.0,0.0))",
                        "kind((0.0D0,0.0D0))",
                        "kind(.true.)",
                        ]))

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

            call open_map_file(iserr)
            if (iserr .ne. 0) then
                print *, errmsg
                stop 1
            endif
            call lookup_integer(kind(0), "fwrap_default_integer", iserr)
            if (iserr .ne. 0) then
                goto 100
            endif
            call lookup_real(kind(0.0), "fwrap_default_real", iserr)
            if (iserr .ne. 0) then
                goto 100
            endif
            call lookup_logical(kind(.true.), "fwrap_default_logical", iserr)
            if (iserr .ne. 0) then
                goto 100
            endif
            call lookup_complex(kind((0.0,0.0)), "fwrap_default_complex", iserr)
            if (iserr .ne. 0) then
                goto 100
            endif
            call lookup_character(kind('a'), "fwrap_default_character", iserr)
            if (iserr .ne. 0) then
                goto 100
            endif
            goto 200
            100 print *, errmsg
            call close_map_file(iserr)
            stop 1
            200 call close_map_file(iserr)
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

if __name__ == '__main__':
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
    gc.generate_genconfig(ctps, buf)
    print buf.getvalue()
