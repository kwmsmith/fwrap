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
        return "end %s %s" % (self.kind, self.name)

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
        return '%s %s(%s) bind(c, name="%s")' % \
                (self.kind, self.name,
                        ', '.join(self.extern_arg_list()),
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

class FunctionWrapper(ProcWrapper):

    def __init__(self, wrapped):
        self.kind = 'function'
        self.name = constants.PROC_SUFFIX_TMPL % wrapped.name
        self.wrapped = wrapped
        ra = pyf.Argument(name=self.name,
                dtype=wrapped.return_arg.dtype,
                intent='out', is_return_arg=True)
        self.arg_man = ArgWrapperManager(wrapped.args, ra)

    def return_spec_declaration(self):
        return self.arg_man.return_spec_declaration()

    def proc_result_name(self):
        return self.arg_man.return_var_name()

class SubroutineWrapper(ProcWrapper):

    def __init__(self, wrapped):
        self.kind = 'subroutine'
        self.name = constants.PROC_SUFFIX_TMPL % wrapped.name
        self.wrapped = wrapped
        self.arg_man = ArgWrapperManager(wrapped.args)

class ArgWrapperManager(object):
    
    def __init__(self, args, return_arg=None):
        self._orig_args = args
        self._orig_return_arg = return_arg
        self.arg_wrappers = None
        self.return_arg_wrapper = None
        self._gen_wrappers()

    def _gen_wrappers(self):
        wargs = []
        for arg in self._orig_args:
            wargs.append(ArgWrapperFactory(arg))
        self.arg_wrappers = wargs
        arg = self._orig_return_arg
        if arg:
            self.return_arg_wrapper = ArgWrapperFactory(arg)

    def call_arg_list(self):
        cl = []
        for argw in self.arg_wrappers:
            cl.append(argw.intern_name())
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
        if self.return_arg_wrapper is None:
            return 'void'
        else:
            return self.return_arg_wrapper.get_ktp()

    def arg_declarations(self):
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.extern_declarations())
        if self.return_arg_wrapper:
            decls.extend(self.return_arg_wrapper.extern_declarations())
        return decls

    def __return_spec_declaration(self):
        #XXX: demeter ???
        return self.return_arg_wrapper.extern_arg.declaration()

    def temp_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.intern_declarations())
        if self.return_arg_wrapper:
            decls.extend(self.return_arg_wrapper.intern_declarations())
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
        if self.return_arg_wrapper:
            wpprs.append(self.return_arg_wrapper)
        for argw in wpprs:
            pcc = argw.post_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def return_var_name(self):
        return self.return_arg_wrapper.intern_name()

def ArgWrapperFactory(arg):
    if getattr(arg, 'dimension', None):
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
        self._extern_args = []
        self._dims = arg.dimension
        self._set_extern_args()

    def _set_extern_args(self):
        orig_name = self._orig_arg.name
        for idx, dim in enumerate(self._dims):
            self._extern_args.append(pyf.Argument(name='%s_d%d' % (orig_name, idx+1),
                                              dtype=pyf.dim_dtype,
                                              intent='in'))
        dims = [dim.name for dim in self._extern_args]
        self._extern_args.append(pyf.Argument(name=orig_name, dtype=self._orig_arg.dtype,
                                          intent=self._orig_arg.intent,
                                          dimension=dims))

    def get_ktp(self):
        return self._extern_args[-1].ktp

    def get_ndims(self):
        return len(self._dims)

    def extern_declarations(self):
        return [arg.declaration() for arg in self._extern_args]

    def c_declarations(self):
        return [arg.c_declaration() for arg in self._extern_args]

    def intern_name(self):
        return self._extern_args[-1].name

    def extern_arg_list(self):
        return [arg.name for arg in self._extern_args]

    def _get_intent(self):
        return self._orig_arg.intent

    intent = property(_get_intent)

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
