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


class Var(object):
    def __init__(self, name, dtype):
        self.name = name
        self.dtype = dtype

class Argument(object):
    def __init__(self, var, intent=None):
        self._var = var
        self.intent = intent

    def _get_name(self):
        return self._var.name

    def _get_dtype(self):
        return self._var.dtype

    name = property(_get_name)
    dtype = property(_get_dtype)

class ProcArgument(object):
    def __init__(self, proc):
        self.proc = proc
        self.name = proc.name

class Dtype(object):
    def __init__(self, type, ktp, dimension=None):
        self.type = type
        self.ktp = ktp

class ArgManager(object):
    
    def __init__(self, args):
        self.args = args

class Procedure(object):

    def __init__(self, name, args):
        super(Procedure, self).__init__()
        self.name = name
        self.args = args
        # self.amgr = ArgManager(args)

class Function(Procedure):
    
    def __init__(self, name, args, return_type):
        super(Function, self).__init__(name, args)
        self.return_type = return_type
        self.kind = 'function'

    def __eq__(self, other):
        return self.name == other.name and \
               self.args == other.args and \
               self.return_type == other.return_type

class FunctionWrapper(Function):
    @classmethod
    def from_proc(cls, name, wrapped):
        self = cls(name, wrapped.args, wrapped.return_type)
        self.wrapped = wrapped
        return self

    def __init__(self, name, args, return_type):
        super(FunctionWrapper, self).__init__(name, args, return_type)

class Subroutine(Procedure):

    def __init__(self, name, args):
        super(Subroutine, self).__init__(name, args)
        self.kind = 'subroutine'

class SubroutineWrapper(Subroutine):

    @classmethod
    def from_proc(cls, name, wrapped):
        self = cls(name, wrapped.args)
        self.wrapped = wrapped
        return self

    def __init__(self, name, args):
        super(SubroutineWrapper, self).__init__(name, args)

class Module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class Use(object):

    def __init__(self, mod, only=None):
        pass
