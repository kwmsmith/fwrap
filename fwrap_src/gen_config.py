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
                            type_decl=ctp.odecl,
                            fwrap_name=ctp.fwrap_name))
    buf.write(dumps(out_lst))

class ConfigTypeParam(object):

    def __init__(self, basetype, odecl, fwrap_name):
        self.basetype = basetype
        self.odecl = odecl
        self.fwrap_name = fwrap_name

    def generate_call(self, buf):
        templ = 'call lookup_%(basetype)s(%(odecl)s, "%(fwrap_name)s", iserr)'
        buf.putln(templ % self.__dict__)

    @classmethod
    def from_dtypes(cls, dtypes):
        ret = []
        for dtype in dtypes:
            if dtype.odecl is None:
                continue
            ret.append(cls(basetype=dtype.type,
                           fwrap_name=dtype.fw_ktp,
                           odecl=dtype.odecl))
        return ret

    def __eq__(self, other):
        return self.basetype == other.basetype and \
                self.odecl == other.odecl and \
                self.fwrap_name == other.fwrap_name

def put_preamble(buf):
    code = '''\
use fc_type_map
implicit none
integer :: iserr
iserr = 0
'''
    buf.putlines(code)
    buf.putempty()

def put_open_map_file(buf):
    code = '''\
call open_map_file(iserr)
if (iserr .ne. 0) then
    print *, errmsg
    stop 1
endif
'''
    buf.putlines(code)

def put_lu_calls(ctps, buf):
    errcode = '''\
if (iserr .ne. 0) then
    goto %d
endif
''' % ERR_LABEL

    for ctp in ctps:
        ctp.generate_call(buf)
        buf.putlines(errcode)

def put_error_handle(buf):
    code = '''\
goto %d
%d print *, errmsg
call close_map_file(iserr)
stop 1
''' % (NON_ERR_LABEL, ERR_LABEL)
    buf.putlines(code)

def put_close_map_file(buf):
    buf.putln('%d call close_map_file(iserr)' % NON_ERR_LABEL)


def generate_genconfig_main(ctps, buf):
    buf.putln("program genconfig")
    buf.indent()
    put_preamble(buf)
    put_open_map_file(buf)
    put_lu_calls(ctps, buf)
    put_error_handle(buf)
    put_close_map_file(buf)
    buf.dedent()
    buf.putln("end program genconfig")

def generate_genconfig(ast, buf):
    ctps = extract_ctps(ast)
    buf.write(fc_type_map_code)
    buf.putempty()
    generate_genconfig_main(ctps, buf)

def extract_ctps(ast):
    dtypes = set()
    for proc in ast:
        dtypes.update(proc.all_dtypes())
    dtypes = list(dtypes)
    return ConfigTypeParam.from_dtypes(dtypes)

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

  character(*), parameter :: NEG_KTP = &
  "genconfig: kind is negative."

  character(*), parameter :: NO_C_TYPE = &
  "genconfig: no corresponding c type."

  character(len=100) :: errmsg

  integer, parameter :: mapping_file_unit = 19

  character(*), parameter :: map_file_name = "%(MAP_SRC)s"

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
        errmsg = NEG_KTP // "[" // alias // "]"
        return
    endif

    if (real_kind .eq. c_float) then
        call write_map(alias, "c_float", iserr)
        return
    else if (real_kind .eq. c_double) then
        call write_map(alias, "c_double", iserr)
        return
    else if (real_kind .eq. c_long_double) then
        call write_map(alias, "c_long_double", iserr)
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        errmsg = NO_C_TYPE // "[" // alias // "]"
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
        errmsg = NEG_KTP // "[" // alias // "]"
        return
    endif

    if (int_kind .eq. c_signed_char) then
        call write_map(alias, "c_signed_char", iserr)
        return
    else if (int_kind .eq. c_short) then
        call write_map(alias, "c_short", iserr)
        return
    else if (int_kind .eq. c_int) then
        call write_map(alias, "c_int", iserr)
        return
    else if (int_kind .eq. c_long) then
        call write_map(alias, "c_long", iserr)
        return
    else if (int_kind .eq. c_long_long) then
        ! XXX assumes C99 long long type exists
        call write_map(alias, "c_long_long", iserr)
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        errmsg = NO_C_TYPE // "[" // alias // "]"
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
        errmsg = NEG_KTP // "[" // alias // "]"
        return
    endif

    if (char_kind .eq. c_char) then
        call write_map(alias, "c_char", iserr)
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        errmsg = NO_C_TYPE // "[" // alias // "]"
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
        errmsg = NEG_KTP // "[" // alias // "]"
        return
    endif

!    if (log_kind .eq. c_bool) then
!        fort_kind_str = "c_bool"
!        c_type_str = "_Bool"
!        return
     if (log_kind .eq. c_signed_char) then
        call write_map(alias, "c_signed_char", iserr)
        return
    else if (log_kind .eq. c_short) then
        call write_map(alias, "c_short", iserr)
        return
    else if (log_kind .eq. c_int) then
        call write_map(alias, "c_int", iserr)
        return
    else if (log_kind .eq. c_long) then
        call write_map(alias, "c_long", iserr)
        return
    else if (log_kind .eq. c_long_long) then
        ! XXX assumes C99 long long type exists
        call write_map(alias, "c_long_long", iserr)
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        errmsg = NO_C_TYPE // "[" // alias // "]"
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
        errmsg = NEG_KTP // "[" // alias // "]"
        return
    endif

    if (complex_kind .eq. c_float_complex) then
        call write_map(alias, "c_float_complex", iserr)
        return
    else if (complex_kind .eq. c_double_complex) then
        call write_map(alias, "c_double_complex", iserr)
        return
    else if (complex_kind .eq. c_long_double_complex) then
        call write_map(alias, "c_long_double_complex", iserr)
        return
    else
        ! No corresponding interoperable type, set error.
        iserr = 1
        errmsg = NO_C_TYPE // "[" // alias // "]"
        return
    end if

  end subroutine lookup_complex

  subroutine write_map(alias, c_name, iserr)
    implicit none
    integer, intent(out) :: iserr
    character(len=*), intent(in) :: alias, c_name

    write(unit=mapping_file_unit, fmt="(3A)", iostat=iserr) alias, " ", c_name

    if (iserr .ne. 0) then
        errmsg = "genconfig: error writing to file %(MAP_SRC)s"
    endif

  end subroutine write_map

  subroutine open_map_file(iserr)
    implicit none
    integer, intent(out) :: iserr
    logical :: exists
    character(len=3) :: status

    errmsg = ""

    inquire(file=map_file_name, exist=exists)

    if (exists) then
        status='OLD'
    else
        status='NEW'
    endif

    open(unit=mapping_file_unit, file=map_file_name,&
            status=status, form='FORMATTED',&
            action='WRITE', position='APPEND', iostat=iserr)

    if (iserr .ne. 0) then
        errmsg = "genconfig: unable to open '%(MAP_SRC)s', aborting."
    endif

  end subroutine open_map_file

  subroutine close_map_file(iserr)
    implicit none
    integer, intent(out) :: iserr

    close(unit=mapping_file_unit, iostat=iserr)

    if (iserr .ne. 0) then
        errmsg = "genconfig: unable to close '%(MAP_SRC)s', aborting."
    endif

  end subroutine close_map_file

end module fc_type_map
''' % {'MAP_SRC' : constants.MAP_SRC}
