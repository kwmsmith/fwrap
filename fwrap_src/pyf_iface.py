class Dtype(object):

    def type_spec(self):
        return '%s(%s)' % (self.type, self.ktp)

class IntegerType(Dtype):
    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'integer'

default_integer = IntegerType(ktp='fwrap_default_int')

class LogicalType(Dtype):
    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'logical'

default_logical = LogicalType(ktp='fwrap_default_logical')

class RealType(Dtype):
    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'real'

default_real = RealType(ktp='fwrap_default_real')
default_dbl  = RealType(ktp='fwrap_default_double')

class ComplexType(Dtype):
    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'complex'

default_complex = ComplexType(ktp='fwrap_default_complex')
default_double_complex = ComplexType(ktp='fwrap_default_dbl_cmplx')

class Var(object):
    def __init__(self, name, dtype, dimension=None):
        self.name = name
        self.dtype = dtype
        self.dimension = dimension

    def var_specs(self):
        specs = [self.dtype.type_spec()]
        if self.dimension:
            specs.append('dimension(%s)' % ', '.join(self.dimension))
        return specs

    def declaration(self):
        return '%s :: %s' % (', '.join(self.var_specs()), self.name)

class Argument(object):

    def __init__(self, name, dtype, intent=None, dimension=None, is_return_arg=False):
        self._var = Var(name=name, dtype=dtype, dimension=dimension)
        self.intent = intent
        self.is_return_arg = is_return_arg

    def _get_name(self):
        return self._var.name

    def _get_dtype(self):
        return self._var.dtype

    def _get_dimension(self):
        return self._var.dimension

    name = property(_get_name)
    dtype = property(_get_dtype)
    dimension = property(_get_dimension)

    def declaration(self):
        var = self._var
        specs = var.var_specs()
        if self.intent and not self.is_return_arg:
            specs.append('intent(%s)' % self.intent)
        return '%s :: %s' % (', '.join(specs), self.name)

class ProcArgument(object):
    def __init__(self, proc):
        self.proc = proc
        self.name = proc.name

def ArgWrapperFactory(arg):
    #XXX: demeter
    if arg.dtype.type == 'logical':
        return LogicalWrapper(arg)
    if getattr(arg, 'dimension', None):
        return ArrayArgWrapper(arg)
    else:
        return ArgWrapper(arg)

class ArgWrapper(object):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_arg = arg
        self._intern_var = None

    def pre_call_code(self):
        return None

    def post_call_code(self):
        return None

    def intern_name(self):
        if self._intern_var:
            return self._intern_var.name
        else:
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

class ArrayArgWrapper(object):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_args = []
        self._intern_vars = []
        self._dims = arg.dimension
        self._set_extern_args()

    def _set_extern_args(self):
        orig_name = self._orig_arg.name
        for idx, dim in enumerate(self._dims):
            self._extern_args.append(Argument(name='%s_d%d' % (orig_name, idx+1),
                                              dtype=default_integer,
                                              intent='in'))
        dims = [dim.name for dim in self._extern_args]
        self._extern_args.append(Argument(name=orig_name, dtype=self._orig_arg.dtype,
                                          intent=self._orig_arg.intent,
                                          dimension=dims))

    def extern_declarations(self):
        return [arg.declaration() for arg in self._extern_args]

    def intern_declarations(self):
        return []

    def pre_call_code(self):
        return []

    def post_call_code(self):
        return []

    def intern_name(self):
        return self._extern_args[-1].name

    def extern_arg_list(self):
        return [arg.name for arg in self._extern_args]

class LogicalWrapper(ArgWrapper):

    def __init__(self, arg):
        super(LogicalWrapper, self).__init__(arg)
        dt = default_integer
        self._extern_arg = Argument(name=arg.name, dtype=dt, intent=arg.intent, is_return_arg=arg.is_return_arg)
        self._intern_var = Var(name=arg.name+'_tmp', dtype=arg.dtype)

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
            cl.append(argw.intern_name())
        return cl

    def extern_arg_list(self):
        ret = []
        for argw in self.arg_wrappers:
            ret.extend(argw.extern_arg_list())
        return ret

    def extern_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.extern_declarations())
        if self.return_arg_wrapper:
            decls.extend(self.return_arg_wrapper.extern_declarations())
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
