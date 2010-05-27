import constants

def generate_pyx(program_unit_list, buf):
    buf.write('''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func():
    return DP_c.empty_func_c()
'''
)

def generate_pxd(program_unit_list, buf):
    buf.write('''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func()
'''
)

class CyArgWrapper(object):

    def __init__(self, arg):
        self.arg = arg

    def extern_declarations(self):
        if self.arg.intent in ('in', 'inout', None):
            return ["%s %s" % (self.arg.get_ktp(), self.arg.get_name())]
        return []

    def intern_declarations(self):
        if self.arg.intent == 'out':
            return ["cdef %s %s" % (self.arg.get_ktp(), self.arg.get_name())]
        return []

    def intern_name(self):
        return self.arg.get_name()

    def call_arg_list(self):
        return ["&%s" % self.arg.get_name()]

    def get_name(self):
        return self.arg.get_name()

    def post_call_code(self):
        return []

    def pre_call_code(self):
        return []

    def return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.arg.get_name()]
        return []


class CyArrayArgWrapper(object):

    def __init__(self, arg):
        self.arg = arg

    def extern_declarations(self):
        return ['object %s' % self.arg.intern_name()]

    def intern_declarations(self):
        return ["cdef np.ndarray[%s, ndim=%d, mode='fortran'] %s_ = %s" % \
                (self.arg.get_ktp(),
                 self.arg.get_ndims(),
                 self.arg.intern_name(),
                 self.arg.intern_name())
                ]
                 
    def call_arg_list(self):
        shapes = reversed(['&%s_.shape[%d]' % (self.arg.intern_name(), i) \
                                for i in range(self.arg.get_ndims())])
        data = '<%s*>%s_.data' % (self.arg.get_ktp(), self.arg.intern_name())
        return list(shapes) + [data]

FW_RETURN_VAR_NAME = 'fwrap_return_var'
class CyArgWrapperManager(object):

    def __init__(self, args, return_type_name):
        self.args = args
        self.return_type_name = return_type_name

    @classmethod
    def from_fwrapped_proc(cls, fw_proc):
        fw_arg_man = fw_proc.arg_man
        args = []
        for fw_arg in fw_arg_man.arg_wrappers:
            if fw_arg.is_array:
                args.append(CyArrayArgWrapper(fw_arg))
            else:
                args.append(CyArgWrapper(fw_arg))
        return_wpr = fw_arg_man.return_arg_wrapper
        rtn = 'object'
        if return_wpr:
            rtn = return_wpr.get_ktp()
        return cls(args=args, return_type_name=rtn)

    def call_arg_list(self):
        cal = []
        for arg in self.args:
            cal.extend(arg.call_arg_list())
        return cal

    def arg_declarations(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.extern_declarations())
        return decls

    def intern_declarations(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.intern_declarations())
        return decls

    def return_arg_declaration(self):
        return ["cdef %s %s" % (self.return_type_name, FW_RETURN_VAR_NAME)]

    def return_tuple_list(self):
        rtl = []
        for arg in self.args:
            rtl.extend(arg.return_tuple_list())
        return rtl

def wrap_fc(ast):
    ret = []
    for proc in ast:
        ret.append(ProcWrapper(wrapped=proc))
    return ret

def generate_cy_pxd(ast, fc_pxd_name, buf):
    buf.putln("from %s cimport *" % fc_pxd_name)
    buf.putln('')
    for proc in ast:
        buf.putln(proc.cy_prototype())

def generate_cy_pyx(ast, buf):
    for proc in ast:
        proc.generate_wrapper(buf)

class ProcWrapper(object):
    
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.name = self.wrapped.wrapped_name()
        self.arg_mgr = CyArgWrapperManager.from_fwrapped_proc(wrapped)

    def cy_prototype(self):
        template = "cpdef api object %(proc_name)s(%(arg_list)s)"
        arg_list = ', '.join(self.arg_mgr.arg_declarations())
        sdict = dict(proc_name=self.name,
                arg_list=arg_list)
        return template % sdict

    def proc_declaration(self):
        return "%s:" % self.cy_prototype()

    def proc_call(self):
        proc_call = "%(call_name)s(%(call_arg_list)s)" % {
                'call_name' : self.wrapped.name,
                'call_arg_list' : ', '.join(self.arg_mgr.call_arg_list())}
        if self.wrapped.kind == 'subroutine':
            return proc_call
        else:
            return '%s = %s' % (FW_RETURN_VAR_NAME, proc_call)

    def temp_declarations(self):
        decls = self.arg_mgr.intern_declarations()
        if self.wrapped.kind == 'function':
            decls.extend(self.arg_mgr.return_arg_declaration())
        return decls

    def return_tuple(self):
        ret_arg_list = []
        if self.wrapped.kind == 'function':
            ret_arg_list.append(FW_RETURN_VAR_NAME)
        ret_arg_list.extend(self.arg_mgr.return_tuple_list())
        return "return (%s,)" % ", ".join(ret_arg_list)

    def generate_wrapper(self, buf):
        buf.putln(self.proc_declaration())
        buf.indent()
        for decl in self.temp_declarations():
            buf.putln(decl)
        buf.putln(self.proc_call())
        buf.putln(self.return_tuple())
        buf.dedent()
