from fwrap_src import pyf_iface as pyf
from fwrap_src import constants

# TODO:
#       separate out fortran/pxd/c header methods into classes

def wrap_pyf_iface(ast):
    fc_wrapper = []
    for proc in ast:
        if proc.kind == 'function':
            fc_wrapper.append(FunctionWrapper(wrapped=proc))
        elif proc.kind == 'subroutine':
            fc_wrapper.append(SubroutineWrapper(wrapped=proc))
        else:
            raise ValueError("object not function or subroutine, %s" % proc)
    return fc_wrapper

def generate_fc_pxd(ast, fc_header_name, buf):
    buf.putln("from %s cimport *" % constants.KTP_PXD_HEADER_SRC.split('.')[0])
    buf.putln('')
    buf.putln('cdef extern from "%s":' % fc_header_name)
    buf.indent()
    for proc in ast:
        buf.putln(proc.cy_prototype())
    buf.dedent()

def generate_fc_h(ast, ktp_header_name, buf):
    buf.putln('#include "%s"' % ktp_header_name)
    buf.putln('')
    for proc in ast:
        buf.putln(proc.c_prototype())

def generate_interface(proc, buf, gmn=constants.KTP_MOD_NAME):
        buf.putln('interface')
        buf.indent()
        buf.putln(proc.proc_declaration())
        buf.indent()
        proc.proc_preamble(gmn, buf)
        buf.dedent()
        buf.putln(proc.proc_end())
        buf.dedent()
        buf.putln('end interface')

class ProcWrapper(object):

    def wrapped_name(self):
        return self.wrapped.name

    def proc_end(self):
        return "end subroutine %s" % self.name

    def proc_preamble(self, ktp_mod, buf):
        buf.putln('use %s' % ktp_mod)
        buf.putln('implicit none')
        for declaration in self.arg_declarations():
            buf.putln(declaration)

    def generate_wrapper(self, buf, gmn=constants.KTP_MOD_NAME):
        buf.putln(self.proc_declaration())
        buf.indent()
        self.proc_preamble(gmn, buf)
        generate_interface(self.wrapped, buf, gmn)
        self.temp_declarations(buf)
        self.pre_call_code(buf)
        self.proc_call(buf)
        self.post_call_code(buf)
        buf.dedent()
        buf.putln(self.proc_end())

    def proc_declaration(self):
        return 'subroutine %s(%s) bind(c, name="%s")' % \
                (self.name, ', '.join(self.extern_arg_list()),
                        self.name)

    def temp_declarations(self, buf):
        for declaration in self.arg_man.temp_declarations():
            buf.putln(declaration)

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def pre_call_code(self, buf):
        for line in self.arg_man.pre_call_code():
            buf.putln(line)

    def post_call_code(self, buf):
        for line in self.arg_man.post_call_code():
            buf.putln(line)

    def proc_call(self, buf):
        proc_call = "%s(%s)" % (self.wrapped.name,
                                ', '.join(self.call_arg_list()))
        if isinstance(self, SubroutineWrapper):
            buf.putln("call %s" % proc_call)
        elif isinstance(self, FunctionWrapper):
            buf.putln("%s = %s" % (self.proc_result_name(), proc_call))

    def call_arg_list(self):
        return self.arg_man.call_arg_list()

    def c_prototype(self):
        return "%s;" % self.cy_prototype()

    def cy_prototype(self):
        args = ", ".join(self.arg_man.c_proto_args())
        return '%s %s(%s)' % (self.arg_man.c_proto_return_type(), self.name, args)

    def all_dtypes(self):
        return self.wrapped.all_dtypes()

class FunctionWrapper(ProcWrapper):

    RETURN_ARG_NAME = 'fw_ret_arg'

    def __init__(self, wrapped):
        self.name = constants.PROC_SUFFIX_TMPL % wrapped.name
        self.wrapped = wrapped
        ra = pyf.Argument(name=self.RETURN_ARG_NAME,
                dtype=wrapped.return_arg.dtype,
                intent='out')
        self.arg_man = ArgWrapperManager([ra] + list(wrapped.args), isfunction=True)

    def return_spec_declaration(self):
        return self.arg_man.return_spec_declaration()

    def proc_result_name(self):
        return self.RETURN_ARG_NAME

class SubroutineWrapper(ProcWrapper):

    def __init__(self, wrapped):
        self.name = constants.PROC_SUFFIX_TMPL % wrapped.name
        self.wrapped = wrapped
        self.arg_man = ArgWrapperManager(wrapped.args, isfunction=False)

class ArgWrapperManager(object):
    
    def __init__(self, args, isfunction):
        self._orig_args = args
        self.isfunction = isfunction
        self.arg_wrappers = None
        self._gen_wrappers()

    def _gen_wrappers(self):
        wargs = []
        for arg in self._orig_args:
            wargs.append(ArgWrapperFactory(arg))
        self.arg_wrappers = wargs

    def call_arg_list(self):
        cl = []
        if not self.isfunction:
            for argw in self.arg_wrappers:
                cl.append(argw.intern_name())
        else:
            cl = [argw.intern_name() for argw in self.arg_wrappers 
                    if argw.intern_name() != FunctionWrapper.RETURN_ARG_NAME]
        return cl

    def extern_arg_list(self):
        ret = []
        for argw in self.arg_wrappers:
            ret.extend(argw.extern_arg_list())
        return ret

    def c_proto_args(self):
        ret = []
        for argw in self.arg_wrappers:
            ret.extend(argw.c_declarations())
        return ret

    def c_proto_return_type(self):
        return 'void'

    def arg_declarations(self):
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.extern_declarations())
        return decls

    def __return_spec_declaration(self):
        #XXX: demeter ???
        return self.return_arg_wrapper.extern_arg.declaration()

    def temp_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.intern_declarations())
        return decls

    def pre_call_code(self):
        all_pcc = []
        for argw in self.arg_wrappers:
            pcc = argw.pre_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def post_call_code(self):
        all_pcc = []
        wpprs = self.arg_wrappers[:]
        for argw in wpprs:
            pcc = argw.post_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def _return_var_name(self):
        return self.return_arg_wrapper.intern_name()

def ArgWrapperFactory(arg):
    if getattr(arg, 'dimension', None):
        if arg.dtype.type == 'character':
            return CharArrayArgWrapper(arg)
        return ArrayArgWrapper(arg)
    elif arg.intent == 'hide':
        return HideArgWrapper(arg)
    elif arg.dtype.type == 'character':
        return CharArgWrapper(arg)
    else:
        return ArgWrapper(arg)

class ArgWrapperBase(object):

    is_array = False

    def pre_call_code(self):
        return []

    def post_call_code(self):
        return []

    def intern_declarations(self):
        return []

    def c_declarations(self):
        return []

class ArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self._extern_arg = arg
        self._intern_var = None
        self.dtype = self._extern_arg.dtype

    def intern_name(self):
        if self._intern_var:
            return self._intern_var.name
        else:
            return self._extern_arg.name

    def get_ktp(self):
        return self._extern_arg.ktp

    def get_name(self):
        return self._extern_arg.name

    def extern_arg_list(self):
        return [self._extern_arg.name]

    def extern_declarations(self):
        return [self._extern_arg.declaration()]

    def intern_declarations(self):
        if self._intern_var:
            return [self._intern_var.declaration()]
        else:
            return []

    def c_declarations(self):
        return [self._extern_arg.c_declaration()]

    def _get_intent(self):
        return self._extern_arg.intent

    intent = property(_get_intent)


class CharArgWrapper(ArgWrapperBase):

    _transfer_templ = '%s = transfer(%s, %s)'

    def __init__(self, arg):
        self.intern_arg = pyf.Argument(name="fw_%s" % arg.name,
                                       dtype=arg.dtype,
                                       intent=arg.intent)
        self.len_arg = pyf.Argument(name="fw_%s_len" % arg.name,
                                    dtype=pyf.dim_dtype,
                                    intent='in')
        self.extern_arg = pyf.Argument(name=arg.name,
                                       dtype=arg.dtype,
                                       intent='inout',
                                       dimension=[self.len_arg.name])
        self.dtype = self.intern_arg.dtype

    def is_assumed_size(self):
        return self.intern_arg.dtype.len == '*'

    def c_declarations(self):
        return [self.len_arg.c_declaration(),
                self.extern_arg.c_declaration()]

    def extern_arg_list(self):
        return [self.len_arg.name,
                self.extern_arg.name]

    def _get_intent(self):
        return self.intern_arg.intent

    intent = property(_get_intent)

    def extern_declarations(self):
        return [self.len_arg.declaration(),
                self.extern_arg.declaration()]

    def intern_declarations(self):
        if self.is_assumed_size():
            return [self.intern_arg._var.declaration(len=self.len_arg.name)]
        return [self.intern_arg._var.orig_declaration()]

    def pre_call_code(self):
        return [self._transfer_templ % (self.intern_arg.name,
                                        self.extern_arg.name,
                                        self.intern_arg.name)]

    def post_call_code(self):
        return [self._transfer_templ % (self.extern_arg.name,
                                           self.intern_arg.name,
                                           self.extern_arg.name)]

    def get_name(self):
        return self.extern_arg.name

    def intern_name(self):
        return self.intern_arg.name

    def get_ktp(self):
        return self.extern_arg.ktp


class HideArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_arg = None
        self._intern_var = \
                pyf.Var(name=arg.name, dtype=arg.dtype, dimension=None)
        self.value = arg.value
        assert self.value is not None

    def intern_name(self):
        return self._intern_var.name

    def extern_arg_list(self):
        return []

    def extern_declarations(self):
        return []

    def intern_declarations(self):
        return [self._intern_var.declaration()]

    def pre_call_code(self):
        return ["%s = (%s)" % (self._intern_var.name, self.value)]


class ArrayArgWrapper(ArgWrapperBase):

    is_array = True

    def __init__(self, arg):
        self._orig_arg = arg
        self.dtype = arg.dtype
        self._arr_dims = []
        self._intern_arr = None
        self._dims = arg.dimension
        self._set_extern_args(ndims=len(self._dims))

    def _set_extern_args(self, ndims):
        orig_name = self._orig_arg.name
        for idx in range(ndims):
            self._arr_dims.append(pyf.Argument(name='%s_d%d' % (orig_name, idx+1),
                                              dtype=pyf.dim_dtype,
                                              intent='in'))
        dims = [dim.name for dim in self._arr_dims]
        self._intern_arr = pyf.Argument(name=orig_name, dtype=self._orig_arg.dtype,
                                          intent=self._orig_arg.intent,
                                          dimension=dims)

    def get_ktp(self):
        return self._intern_arr.ktp

    def get_ndims(self):
        return len(self._dims)

    def extern_declarations(self):
        return [arg.declaration() for arg in self._arr_dims] + \
                [self._intern_arr.declaration()]

    def c_declarations(self):
        return [arg.c_declaration() for arg in self._arr_dims] + \
                [self._intern_arr.c_declaration()]

    def intern_name(self):
        return self._intern_arr.name

    def extern_arg_list(self):
        return [arg.name for arg in self._arr_dims] + \
                [self._intern_arr.name]

    def _get_intent(self):
        return self._orig_arg.intent

    intent = property(_get_intent)

class CharArrayArgWrapper(ArrayArgWrapper):

    def __init__(self, arg):
        super(CharArrayArgWrapper, self).__init__(arg)
        # regenerate dims to account for character string length
        self._arr_dims = []
        self._set_extern_args(ndims=len(self._dims)+1)
        self._copy_arr = pyf.Argument(name="fw_%s" % self._orig_arg.name,
                                      dtype=self._orig_arg.dtype,
                                      dimension=[dim.name for dim in self._arr_dims[1:]],
                                      intent=None)

    def is_assumed_size(self):
        return self._orig_arg.dtype.len == '*'

    def intern_declarations(self):
        if self.is_assumed_size():
            return [self._copy_arr._var.declaration(len=self._arr_dims[0].name)]
        return [self._copy_arr._var.orig_declaration()]

    def pre_call_code(self):
        tmpl = "%(intern)s = reshape(transfer(%(name)s, %(intern)s), shape(%(intern)s))"
        D = {"intern" : self.intern_name(), "name" : self._orig_arg.name}
        return [tmpl % D]

    def post_call_code(self):
        if self._orig_arg.intent == "in":
            return []
        tmpl = "%(name)s = reshape(transfer(%(intern)s, %(name)s), shape(%(name)s))"
        D = {"intern" : self.intern_name(), "name" : self._orig_arg.name}
        return [tmpl % D]

    def intern_name(self):
        return self._copy_arr.name

class LogicalWrapper(ArgWrapper):

    def __init__(self, arg):
        super(LogicalWrapper, self).__init__(arg)
        dt = pyf.default_integer
        self._extern_arg = pyf.Argument(name=arg.name, dtype=dt, intent=arg.intent, is_return_arg=arg.is_return_arg)
        self._intern_var = pyf.Var(name=arg.name+'_tmp', dtype=arg.dtype)

    def pre_call_code(self):
        pcc = '''\
if(%(extern_arg)s .ne. 0) then
    %(intern_var)s = .true.
else
    %(intern_var)s = .false.
end if
''' % {'extern_arg' : self._extern_arg.name,
       'intern_var' : self._intern_var.name}

        return pcc.splitlines()

    def post_call_code(self):
        pcc = '''\
if(%(intern_var)s) then
    %(extern_arg)s = 1
else
    %(extern_arg)s = 0
end if
''' % {'extern_arg' : self._extern_arg.name,
       'intern_var' : self._intern_var.name}
        return pcc.splitlines()
