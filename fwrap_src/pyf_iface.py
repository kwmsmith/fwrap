

default_integer = object()
default_real = object()
default_complex = object()


class var(object):
    def __init__(self, name, dtype):
        pass

class argument(object):
    def __init__(self, name, dtype, intent):
        self.name = name
        self.dtype = dtype
        self.intent = intent

class dtype(object):
    def __init__(self, type, ktp):
        self.type = type
        self.ktp = ktp

class function(object):
    
    def __init__(self, name, args, return_type):
        self.name = name
        self.args = args
        self.return_type = return_type
        self.kind = self.__class__.__name__

    def __eq__(self, other):
        return self.name == other.name and \
               self.args == other.args and \
               self.return_type == other.return_type

class subroutine(object):

    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.kind = self.__class__.__name__

class module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class use(object):

    def __init__(self, mod, only=None):
        pass
