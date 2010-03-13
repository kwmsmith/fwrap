
def gen_config(spec, buf):
    buf.putln("module config")
    buf.indent()
    buf.putln("use iso_c_binding")
    buf.putln("implicit none")
    for param_name in sorted(spec):
        buf.putln("integer, parameter :: %s = %s" %\
                (param_name, spec[param_name]))
    buf.dedent()
    buf.putln("end module config")
