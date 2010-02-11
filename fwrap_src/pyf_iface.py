

default_integer = object()
default_real = object()
default_complex = object()


class Var(object):
    def __init__(self, name, dtype):
        pass

class Argument(object):
    def __init__(self, name, dtype, intent=None):
        self.name = name
        self.dtype = dtype
        self.intent = intent

class Dtype(object):
    def __init__(self, type, ktp):
        self.type = type
        self.ktp = ktp

class Procedure(object):

    def __init__(self, name, args):
        super(Procedure, self).__init__()
        self.name = name
        self.args = args

class Function(Procedure):
    
    def __init__(self, name, args, return_type):
        super(Function, self).__init__(name, args)
        self.return_type = return_type
        self.kind = 'function'

    def __eq__(self, other):
        return self.name == other.name and \
               self.args == other.args and \
               self.return_type == other.return_type

class WrappedFunction(Function):
    def __init__(self, name, args, wrapped, return_type):
        super(WrappedFunction, self).__init__(name, args, return_type)
        self.wrapped = wrapped

class Subroutine(Procedure):

    def __init__(self, name, args):
        super(Subroutine, self).__init__(name, args)
        self.kind = 'subroutine'

class WrappedSubroutine(Subroutine):
    def __init__(self, name, args, wrapped):
        super(WrappedSubroutine, self).__init__(name, args)
        self.wrapped = wrapped

class Module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class Use(object):

    def __init__(self, mod, only=None):
        pass
