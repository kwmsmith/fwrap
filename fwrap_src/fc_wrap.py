def generate_pxd(program_unit_list, buf):
    buf.write('''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''
)

def generate_h(program_unit_list, buf):
    buf.write('''
#include "config.h"
fwrap_default_int empty_func_c();
'''
)

def generate_fortran(program_unit_list, buf):
    buf.write(
'''
function fw_empty_func() bind(c, name="empty_func_c")
    use iso_c_binding
    implicit none
    integer(c_int) :: fw_empty_func
    interface
        function empty_func()
            implicit none
            integer :: empty_func
        end function empty_func
    end interface
    fw_empty_func = empty_func()
end function fw_empty_func
'''
)
