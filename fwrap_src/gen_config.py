class ConfigTypeParam(object):

    def __init__(self, basetype, ktp, fwrap_name):
        self.basetype = basetype
        self.ktp = ktp
        self.fwrap_name = fwrap_name

    def generate_call(self, buf):
        templ = 'call lookup_%(basetype)s(%(ktp)s, "%(fwrap_name)s", iserr)'
        buf.putln(templ % self.__dict__)

class GenConfigException(Exception):
    pass


def check_params(params):
    for p in params:
        if p not in _C_BINDING_TYPES:
            raise GenConfigException(
                    "%s is not a type parameter "
                    "defined in the ISO C BINDING module." % p)

def preamble(buf):
    buf.putln("module config")
    buf.indent()
    buf.putln("use iso_c_binding")
    buf.putln("implicit none")

def put_param_defs(spec, buf):
    for param_name in sorted(spec):
        buf.putln("integer, parameter :: %s = %s" %\
                (param_name, spec[param_name]))

def postamble(buf):
    buf.dedent()
    buf.putln("end module config")

def gen_config(spec, buf):
    check_params(spec.values())
    preamble(buf)
    put_param_defs(spec, buf)
    postamble(buf)

_C_BINDING_TYPES = (
        "c_char",
        "c_signed_char",
        "c_short",
        "c_int",
        "c_long",
        "c_long_long",
        "c_size_t",
        "c_int8_t",
        "c_int16_t",
        "c_int32_t",
        "c_int64_t",
        "c_int_least8_t",
        "c_int_least16_t",
        "c_int_least32_t",
        "c_int_least64_t",
        "c_int_fast8_t",
        "c_int_fast16_t",
        "c_int_fast32_t",
        "c_int_fast64_t",
        "c_intmax_t",
        "c_intptr_t",
        "c_float",
        "c_double",
        "c_long_double",
        "c_complex",
        "c_double_complex",
        "c_long_double_complex",
        "c_bool",
        )
