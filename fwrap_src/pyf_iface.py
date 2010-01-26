

default_integer = object()
default_real = object()
default_complex = object()


class var(object):
    def __init__(self, name, dtype):
        pass

class function(object):
    
    def __init__(self, name, args, return_type):
        self.name = name
        self.args = args
        self.return_type = return_type

class subroutine(object):

    def __init__(self, name, args):
        pass

class module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class use(object):

    def __init__(self, mod, only=None):
        pass
