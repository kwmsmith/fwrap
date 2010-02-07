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

class GenFortranProcedure(object):

    def __init__(self, proc):
        self.kind = proc.kind
        self.name = proc.name
        self.args = proc.args
        self.return_type = proc.return_type

    def procedure_decl(self):
        return "%s %s(%s)" % (self.kind, self.name,
                    ', '.join([arg.name for arg in self.args]))

    def procedure_end(self):
        return "end %s %s" % (self.kind, self.name)

    def generate_interface(self, buf):
        buf.putln('interface')
        buf.indent()
        buf.putln(self.procedure_decl())
        buf.indent()
        buf.putln('use config')
        buf.putln('implicit none')
        self.gen_arg_specs(buf)
        if self.return_type:
            buf.putln(self.get_return_spec())
        buf.dedent()
        buf.putln(self.procedure_end())
        buf.dedent()
        buf.putln('end interface')

    def gen_arg_specs(self, buf):
        for arg in self.args:
            try:
                buf.putln(self.gen_arg_spec(arg.dtype.type,
                                arg.dtype.ktp, arg.name,
                                arg.intent))
            except AttributeError:
                gfp = GenFortranProcedure(arg.dtype).generate_interface(buf)

    def get_return_spec(self):
        return self.gen_arg_spec(self.return_type.type,
                            self.return_type.ktp, self.name)

    def gen_arg_spec(self, type, ktp, name, intent=None):
        spec = ['%s(%s)' % (type, ktp)]
        if intent:
            spec.append('intent(%s)' % intent)
        return '%s :: %s' % (', '.join(spec), name)
