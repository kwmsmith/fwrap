class SourceGenerator(object):

    def __init__(self, basename):
        self.basename = basename
        self.filename = self._fname_template % basename

    def generate(self, program_unit_list, buf):
        raise NotImplementedError()

class GenPxd(SourceGenerator):

    _fname_template = "%s_c.pxd"

    def generate(self, program_unit_list, buf):
        buf.write('''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''
    )

class GenCHeader(SourceGenerator):

    _fname_template = "%s_c.h"

    def generate(self, program_unit_list, buf):
        buf.write('''
#include "config.h"
fwrap_default_int empty_func_c();
'''
    )


class GenFortran(SourceGenerator):

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

    def procedure_decl(self, pro):
        return "%s %s(%s)" % (pro.kind, pro.name, 
                    ', '.join([arg.name for arg in pro.args]))

    def procedure_end(self, pro):
        return "end %s %s" % (pro.kind, pro.name)

    def generate_interface(self, procedure, buf):
        # XXX: this belongs in a visitor or as part of a separate
        # ProcedureGenerator object.
        if procedure.return_type:
            procedure.kind = 'function'
        else:
            procedure.kind = 'subroutine'

        buf.putln('interface')
        buf.indent()
        buf.putln(self.procedure_decl(procedure))
        buf.indent()
        buf.putln('use config')
        buf.putln('implicit none')
        for arg_spec in self.get_arg_specs(procedure.args):
            buf.putln(arg_spec)
        if procedure.return_type:
            buf.putln(self.get_return_spec(procedure))
        buf.dedent()
        buf.putln(self.procedure_end(procedure))
        buf.dedent()
        buf.putln('end interface')

    def get_arg_specs(self, args):
        return [self.gen_arg_spec(arg.dtype.type,
                        arg.dtype.ktp, arg.name,
                        arg.intent) for arg in args]

    def get_return_spec(self, pro):
        return self.gen_arg_spec(pro.return_type.type,
                            pro.return_type.ktp, pro.name)

    def gen_arg_spec(self, type, ktp, name, intent=None):
        spec = ['%s(%s)' % (type, ktp)]
        if intent:
            spec.append('intent(%s)' % intent)
        return '%s :: %s' % (', '.join(spec), name)
