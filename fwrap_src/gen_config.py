class ConfigTypeParam(object):

    def __init__(self, basetype, ktp, fwrap_name):
        self.basetype = basetype
        self.ktp = ktp
        self.fwrap_name = fwrap_name

    def generate_call(self, buf):
        templ = 'call lookup_%(basetype)s(%(ktp)s, "%(fwrap_name)s", iserr)'
        buf.putln(templ % self.__dict__)

def generate_genconfig_main(ctps, buf):
    buf.putln("program genconfig")
    buf.indent()
    buf.putln("use fc_type_map")
    buf.putln("implicit none")
    buf.putln("integer :: iserr")
    buf.putln("iserr = 0")
    for ctp in ctps:
        ctp.generate_call(buf)
    buf.dedent()
    buf.putln("end program genconfig")

def generate_genconfig(ctps, buf):
    buf.write(fc_type_map_code)
    buf.putln('')
    generate_genconfig_main(ctps, buf)

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

fc_type_map_code = '''
module fc_type_map
  use iso_c_binding
  implicit none

  save

  integer :: mapping_file_unit

  contains

  subroutine lookup_real(real_kind, alias, iserr)
    implicit none
    integer, intent(in) :: real_kind
    character(len=*), intent(in) :: alias
    integer, intent(out) :: iserr

    iserr = 0
    ! make sure kind .gt. 0
    if (real_kind .lt. 0) then
        ! set error condition
        iserr = 1
        return
    endif

    if (real_kind .eq. c_float) then
        call write_map(alias, "c_float")
        return
    else if (real_kind .eq. c_double) then
        call write_map(alias, "c_double")
        return
    else if (real_kind .eq. c_long_double) then
        call write_map(alias, "c_long_double")
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        return
    end if

  end subroutine lookup_real

  subroutine lookup_integer(int_kind, alias, iserr)
    implicit none
    integer, intent(in) :: int_kind
    character(len=*), intent(in) :: alias
    integer, intent(out) :: iserr

    iserr = 0
    ! make sure kind .gt. 0
    if (int_kind .lt. 0) then
        ! set error condition
        iserr = 1
        return
    endif

    if (int_kind .eq. c_signed_char) then
        call write_map(alias, "c_signed_char")
        return
    else if (int_kind .eq. c_short) then
        call write_map(alias, "c_short")
        return
    else if (int_kind .eq. c_int) then
        call write_map(alias, "c_int")
        return
    else if (int_kind .eq. c_long) then
        call write_map(alias, "c_long")
        return
    else if (int_kind .eq. c_long_long) then
        ! XXX assumes C99 long long type exists
        call write_map(alias, "c_long_long")
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        return
    end if

  end subroutine lookup_integer

  subroutine lookup_character(char_kind, alias, iserr)
    implicit none
    integer, intent(in) :: char_kind
    character(len=*), intent(in) :: alias
    integer, intent(out) :: iserr

    iserr = 0
    ! make sure kind .gt. 0
    if (char_kind .lt. 0) then
        ! set error condition
        iserr = 1
        return
    endif

    if (char_kind .eq. c_char) then
        call write_map(alias, "c_char")
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        return
    end if

  end subroutine lookup_character

  subroutine lookup_logical(log_kind, alias, iserr)
    ! XXX assumes C99 _Bool.
    implicit none
    integer, intent(in) :: log_kind
    character(len=*), intent(in) :: alias
    integer, intent(out) :: iserr

    iserr = 0
    ! make sure kind .gt. 0
    if (log_kind .lt. 0) then
        ! set error condition
        iserr = 1
        return
    endif

!    if (log_kind .eq. c_bool) then
!        fort_ktp_str = "c_bool"
!        c_type_str = "_Bool"
!        return
     if (log_kind .eq. c_signed_char) then
        call write_map(alias, "c_signed_char")
        return
    else if (log_kind .eq. c_short) then
        call write_map(alias, "c_short")
        return
    else if (log_kind .eq. c_int) then
        call write_map(alias, "c_int")
        return
    else if (log_kind .eq. c_long) then
        call write_map(alias, "c_long")
        return
    else if (log_kind .eq. c_long_long) then
        ! XXX assumes C99 long long type exists
        call write_map(alias, "c_long_long")
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        return
    end if

  end subroutine lookup_logical

  subroutine lookup_complex(complex_kind, alias, iserr)
    ! XXX assumes C99 _Complex.
    implicit none
    integer, intent(in) :: complex_kind
    character(len=*), intent(in) :: alias
    integer, intent(out) :: iserr

    iserr = 0
    ! make sure kind .gt. 0
    if (complex_kind .lt. 0) then
        ! set error condition
        iserr = 1
        return
    endif

    if (complex_kind .eq. c_float_complex) then
        call write_map(alias, "c_float_complex")
        return
    else if (complex_kind .eq. c_double_complex) then
        call write_map(alias, "c_double_complex")
        return
    else if (complex_kind .eq. c_long_double_complex) then
        call write_map(alias, "c_long_double_complex")
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        return
    end if

  end subroutine lookup_complex

  subroutine write_map(alias, c_name)
    implicit none
    character(len=*), intent(in) :: alias, c_name

    write(unit=mapping_file_unit, fmt="(3A)") alias, " ", c_name

  end subroutine write_map

end module fc_type_map
'''
