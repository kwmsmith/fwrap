class SourceGenerator(object):

    def __init__(self, basename):
        self.basename = basename
        self.filename = self._fname_template % basename

    def generate(self, program_unit_list, buf):
        raise NotImplementedError()

class FCWrapPxd(SourceGenerator):

    _fname_template = "%s_c.pxd"

    def generate(self, program_unit_list, buf):
        buf.write('''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''
    )

class FCWrapCHeader(SourceGenerator):

    _fname_template = "%s_c.h"

    def generate(self, program_unit_list, buf):
        buf.write('''
#include "config.h"
fwrap_default_int empty_func_c();
'''
    )


class FCWrapFortran(SourceGenerator):

    _fname_template = "%s_c.f90"

    def generate(self, program_unit_list, buf):
        buf.write('''
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
