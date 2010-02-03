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

    def generate_interface(self, procedure, buf):
        template = '''
interface
    %(proc_type)s %(proc_name)s(%(proc_arglst)s)
        use config
        implicit none%(arg_specs)s
        %(return_spec)s
    end %(proc_type)s %(proc_name)s
end interface
'''
        subst_dict = {}
        subst_dict['proc_type'] = 'function'
        subst_dict['proc_name'] = procedure.name
        subst_dict['proc_arglst'] = ', '.join([arg.name for arg in procedure.args])
        subst_dict['arg_specs'] = self.get_arg_specs(procedure.args)
        subst_dict['return_spec'] = self.get_return_spec(procedure)

        iface = template % subst_dict
        buf.write(iface)

    def get_arg_specs(self, procedure):
        return ''

    def get_return_spec(self, procedure):
        return 'integer(fwrap_default_int) :: empty_func'
