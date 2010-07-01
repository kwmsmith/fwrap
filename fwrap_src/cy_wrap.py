import pyf_iface
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

def CyArgWrapper(arg):
    if isinstance(arg.dtype, pyf_iface.ComplexType):
        return _CyCmplxArg(arg)
    elif isinstance(arg.dtype, pyf_iface.CharacterType):
        return _CyCharArg(arg)
    return _CyArgWrapper(arg)

class _CyArgWrapper(object):

    def __init__(self, arg):
        self.arg = arg

    def cy_dtype_name(self):
        return self.arg.get_ktp()

    def extern_declarations(self):
        if self.arg.intent in ('in', 'inout', None):
            return ["%s %s" % (self.cy_dtype_name(), self.arg.get_name())]
        return []

    def intern_declarations(self):
        if self.arg.intent == 'out':
            return ["cdef %s %s" % (self.cy_dtype_name(), self.arg.get_name())]
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

class _CyCharArg(_CyArgWrapper):

    def __init__(self, arg):
        super(_CyCharArg, self).__init__(arg)
        
    def intern_name(self):
        return 'fw_%s' % self.get_name()

    def intern_len_name(self):
        return '%s_len' % self.intern_name()

    def cy_dtype_name(self):
        return 'bytes'

    def intern_declarations(self):
        return ['cdef bytes %s' % self.intern_name(),
                'cdef fwrap_npy_intp %s' % self.intern_len_name()]

    def get_len(self):
        return int(self.arg.dtype.len)

    def pre_call_code(self):
        ret = []
        if self.arg.intent == 'out':
            ret.append('%s = "%s"' % (self.intern_name(), '0'*self.get_len()))
        elif self.arg.intent == 'in':
            ret.append('%s = %s' % (self.intern_name(), self.get_name()))
        elif self.arg.intent in ('inout', None):
            ret.append('%s = PyBytes_FromStringAndSize(<char*>%s, len(%s))' % \
                    (self.intern_name(), self.get_name(), self.get_name()))
        return ret + ['%s = len(%s)' % (self.intern_len_name(), self.intern_name())]

    def call_arg_list(self):
        return ['&%s' % self.intern_len_name(), '<char*>%s' % self.intern_name()]

    def return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.intern_name()]
        return []

class _CyCmplxArg(_CyArgWrapper):

    def __init__(self, arg):
        super(_CyCmplxArg, self).__init__(arg)
        self.intern_name = 'fw_%s' % self.arg.get_name()
    
    def cy_dtype_name(self):
        return "cy_%s" % self.arg.get_ktp()

    def intern_declarations(self):
        ids = super(_CyCmplxArg, self).intern_declarations()
        return ids + ['cdef %s %s' % (self.arg.get_ktp(), self.intern_name)]

    def pre_call_code(self):
        if self.arg.intent in ('in', 'inout', None):
            d = {'argname' : self.arg.get_name(),
                 'ktp' : self.arg.get_ktp(),
                 'intern_name' : self.intern_name}
            return ['%(ktp)s_from_parts(%(argname)s.real, %(argname)s.imag, %(intern_name)s)' % d]
        return []

    def post_call_code(self):
        if self.arg.intent in ('out', 'inout', None):
            d = {'argname' : self.arg.get_name(),
                 'ktp' : self.arg.get_ktp(),
                 'intern_name' : self.intern_name}
            return ('%(argname)s.real = %(ktp)s_creal(%(intern_name)s)\n'
                    '%(argname)s.imag = %(ktp)s_cimag(%(intern_name)s)' % d).splitlines()
        return []

    def call_arg_list(self):
        return ['&%s' % self.intern_name]

class CyArrayArgWrapper(object):

    def __init__(self, arg):
        self.arg = arg
        self.intern_name = '%s_' % self.arg.intern_name()

    def extern_declarations(self):
        return ['object %s' % self.arg.intern_name()]

    def intern_declarations(self):
        return ["cdef np.ndarray[%s, ndim=%d, mode='fortran'] %s" % \
                (self.arg.get_ktp(),
                 self.arg.get_ndims(),
                 self.intern_name,)
                ]
                 
    def call_arg_list(self):
        shapes = ['<fwrap_npy_intp*>&%s.shape[%d]' % (self.intern_name, i) \
                                for i in range(self.arg.get_ndims())]
        data = '<%s*>%s.data' % (self.arg.get_ktp(), self.intern_name)
        return list(shapes) + [data]

    def pre_call_code(self):
        return ["%s = %s" % (self.intern_name, self.arg.intern_name())]

    def post_call_code(self):
        return []

    def return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.intern_name]
        return []

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

    def pre_call_code(self):
        pcc = []
        for arg in self.args:
            pcc.extend(arg.pre_call_code())
        return pcc

    def post_call_code(self):
        pcc = []
        for arg in self.args:
            pcc.extend(arg.post_call_code())
        return pcc

def wrap_fc(ast):
    ret = []
    for proc in ast:
        ret.append(ProcWrapper(wrapped=proc))
    return ret

def generate_cy_pxd(ast, fc_pxd_name, buf):
    buf.putln('cimport numpy as np')
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

    def temp_declarations(self, buf):
        decls = self.arg_mgr.intern_declarations()
        if self.wrapped.kind == 'function':
            decls.extend(self.arg_mgr.return_arg_declaration())
        for line in decls:
            buf.putln(line)

    def return_tuple(self):
        ret_arg_list = []
        if self.wrapped.kind == 'function':
            ret_arg_list.append(FW_RETURN_VAR_NAME)
        ret_arg_list.extend(self.arg_mgr.return_tuple_list())
        if ret_arg_list:
            return "return (%s,)" % ", ".join(ret_arg_list)
        else:
            return ''

    def pre_call_code(self, buf):
        for line in self.arg_mgr.pre_call_code():
            buf.putln(line)

    def post_call_code(self, buf):
        for line in self.arg_mgr.post_call_code():
            buf.putln(line)

    def generate_wrapper(self, buf):
        buf.putln(self.proc_declaration())
        buf.indent()
        self.temp_declarations(buf)
        self.pre_call_code(buf)
        buf.putln(self.proc_call())
        self.post_call_code(buf)
        rt = self.return_tuple()
        if rt: buf.putln(rt)
        buf.dedent()
