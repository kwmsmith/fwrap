# Specification statements:
# A variable must have a type:
# Base types are integer, real, complex, character, logical.
# Derived types...
# The base type may have a kind type parameter.
# A variable may have these attributes:
# dimension -- list of dimension specs
# 

default_integer = object()
default_real = object()
default_complex = object()

class Dtype(object):
    def __init__(self, type, ktp, dimension=None):
        self.type = type
        self.ktp = ktp

class Var(object):
    def __init__(self, name, dtype):
        self.name = name
        self.dtype = dtype

    def type_spec(self):
        #XXX: demeter
        return '%s(%s)' % (self.dtype.type, self.dtype.ktp)

    def declaration(self):
        return '%s :: %s' % (self.type_spec(), self.name)

class Argument(object):

    def __init__(self, name, dtype, intent=None, is_return_arg=False):
        self._var = Var(name=name, dtype=dtype)
        self.intent = intent
        self.is_return_arg = is_return_arg

    def _get_name(self):
        return self._var.name

    def _get_dtype(self):
        return self._var.dtype

    name = property(_get_name)
    dtype = property(_get_dtype)

    def declaration(self):
        var = self._var
        spec = [var.type_spec()]
        if self.intent and not self.is_return_arg:
            spec.append('intent(%s)' % self.intent)
        return '%s :: %s' % (', '.join(spec), self.name)

class ProcArgument(object):
    def __init__(self, proc):
        self.proc = proc
        self.name = proc.name

def ArgWrapperFactory(arg):
    #XXX: demeter
    if arg.dtype.type == 'logical':
        return LogicalWrapper(arg)
    else:
        return ArgWrapper(arg)

class ArgWrapper(object):

    def __init__(self, arg):
        self._orig_arg = arg
        self.extern_arg = arg
        self.intern_var = None

    def pre_call_code(self):
        return None

    def post_call_code(self):
        return None

    def intern_name(self):
        if self.intern_var:
            return self.intern_var.name
        else:
            return self.extern_arg.name

class LogicalWrapper(ArgWrapper):

    def __init__(self, arg):
        super(LogicalWrapper, self).__init__(arg)
        dt = Dtype(type='integer', ktp='fwrap_default_int')
        self.extern_arg = Argument(name=arg.name, dtype=dt, intent=arg.intent, is_return_arg=arg.is_return_arg)
        self.intern_var = Var(name=arg.name+'_tmp', dtype=arg.dtype)

    def pre_call_code(self):
        pcc = '''\
if(%(extern_arg)s .ne. 0) then
    %(intern_var)s = .true.
else
    %(intern_var)s = .false.
end if
''' % {'extern_arg' : self.extern_arg.name,
       'intern_var' : self.intern_var.name}

        return pcc.splitlines()

    def post_call_code(self):
        pcc = '''\
if(%(intern_var)s) then
    %(extern_arg)s = 1
else
    %(extern_arg)s = 0
end if
''' % {'extern_arg' : self.extern_arg.name,
       'intern_var' : self.intern_var.name}
        return pcc.splitlines()

class ArgManager(object):
    
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
            if argw.intern_var:
                cl.append(argw.intern_var.name)
            else:
                cl.append(argw.extern_arg.name)
        return cl

    def extern_arg_list(self):
        return [argw.extern_arg.name for argw in self.arg_wrappers]

    def extern_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.append(argw.extern_arg.declaration())
        if self.return_arg_wrapper:
            decls.append(self.return_arg_wrapper.extern_arg.declaration())
        return decls

    def arg_declarations(self):
        return self.extern_declarations()

    def __return_spec_declaration(self):
        #XXX: demeter ???
        return self.return_arg_wrapper.extern_arg.declaration()

    def temp_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            if argw.intern_var:
                decls.append(argw.intern_var.declaration())
        if self.return_arg_wrapper:
            if self.return_arg_wrapper.intern_var:
                decls.append(self.return_arg_wrapper.intern_var.declaration())
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
        wpprs = self.arg_wrappers
        if self.return_arg_wrapper:
            wpprs.append(self.return_arg_wrapper)
        for argw in wpprs:
            pcc = argw.post_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def return_var_name(self):
        return self.return_arg_wrapper.intern_name()

class Procedure(object):

    def __init__(self, name, args):
        super(Procedure, self).__init__()
        self.name = name
        self.args = args

class Function(Procedure):
    
    def __init__(self, name, args, return_type):
        super(Function, self).__init__(name, args)
        self.return_arg = Argument(name=name, dtype=return_type, intent='out', is_return_arg=True)
        self.kind = 'function'

    def __eq__(self, other):
        return self.name == other.name and \
               self.args == other.args and \
               self.return_arg == other.return_arg

class Subroutine(Procedure):

    def __init__(self, name, args):
        super(Subroutine, self).__init__(name, args)
        self.kind = 'subroutine'

class ProcWrapper(object):

    #XXX: remove delegate (?)

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def temp_declarations(self):
        return self.arg_man.temp_declarations()

    def pre_call_code(self):
        return self.arg_man.pre_call_code()

    def post_call_code(self):
        return self.arg_man.post_call_code()

    def call_arg_list(self):
        return self.arg_man.call_arg_list()

class FunctionWrapper(ProcWrapper):

    def __init__(self, name, wrapped):
        self.kind = 'function'
        self.name = name
        self.wrapped = wrapped
        #XXX: demeter ???
        ra = Argument(name=name, dtype=wrapped.return_arg.dtype, intent='out', is_return_arg=True)
        self.arg_man = ArgManager(wrapped.args, ra)

    def return_spec_declaration(self):
        return self.arg_man.return_spec_declaration()

    def proc_result_name(self):
        return self.arg_man.return_var_name()

class SubroutineWrapper(ProcWrapper):

    def __init__(self, name, wrapped):
        self.kind = 'subroutine'
        self.name = name
        self.wrapped = wrapped
        self.arg_man = ArgManager(wrapped.args)

class Module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class Use(object):

    def __init__(self, mod, only=None):
        pass
