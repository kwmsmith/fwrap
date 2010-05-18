import re

vfn_matcher = re.compile(r'[a-zA-Z][_a-zA-Z0-9]{,62}$').match
def valid_fort_name(name):
    return vfn_matcher(name)

class InvalidNameException(Exception):
    pass

# TODO: this should be collected together with the KTP_MOD_NAME constant
def ktp_namer(ktp):
    return "fwrap_%s" % ktp

_do_nothing = lambda x: x

class Dtype(object):

    _all_dtypes = {}

    def __new__(cls, ktp, *args, **kwargs):
        if not valid_fort_name(ktp):
            raise InvalidNameException("%s is not a valid fortran parameter name.")
        name = ktp_namer(ktp)
        if name in cls._all_dtypes:
            return cls._all_dtypes[name]
        dt = super(Dtype, cls).__new__(cls)
        cls._all_dtypes[name] = dt
        return dt

    def __init__(self, ktp, orig_ktp=None):
        self.ktp = ktp_namer(ktp)
        self.orig_ktp = orig_ktp
        self.type = None

    def type_spec(self):
        return '%s(%s)' % (self.type, self.ktp)

    @classmethod
    def all_dtypes(cls):
        return list(cls._all_dtypes.values())

class CharacterType(Dtype):
    def __init__(self, ktp, orig_ktp=None):
        super(CharacterType, self).__init__(ktp, orig_ktp)
        self.type = 'character'

default_character = CharacterType(ktp="default_character", orig_ktp="kind('a')")

class IntegerType(Dtype):

    def __init__(self, ktp, orig_ktp=None):
        super(IntegerType, self).__init__(ktp, orig_ktp)
        self.type = 'integer'

default_integer = IntegerType(ktp='default_integer', orig_ktp="kind(0)")

dim_dtype = IntegerType(ktp="npy_intp", orig_ktp=None)

class LogicalType(Dtype):

    def __init__(self, ktp, orig_ktp=None):
        super(LogicalType, self).__init__(ktp, orig_ktp)
        self.type = 'logical'

default_logical = LogicalType(ktp='default_logical', orig_ktp="kind(.true.)")

class RealType(Dtype):

    def __init__(self, ktp, orig_ktp=None):
        super(RealType, self).__init__(ktp, orig_ktp)
        self.type = 'real'

default_real = RealType(ktp='default_real', orig_ktp="kind(0.0)")
default_dbl  = RealType(ktp='default_double', orig_ktp="kind(0.0D0)")

class ComplexType(Dtype):

    def __init__(self, ktp, orig_ktp=None):
        super(ComplexType, self).__init__(ktp, orig_ktp)
        self.type = 'complex'

default_complex = ComplexType(ktp='default_complex', orig_ktp="kind((0.0,0.0))")
default_double_complex = ComplexType(ktp='default_double_complex', orig_ktp="kind((0.0D0,0.0D0))")

class Parameter(object):
    
    def __init__(self, name, dtype, value):
        self.name = name
        self.dtype = dtype
        self.value = value


class Var(object):
    def __init__(self, name, dtype, dimension=None):
        if not valid_fort_name(name):
            raise InvalidNameException("%s is not a valid fortran variable name.")
        self.name = name
        self.dtype = dtype
        self.dimension = dimension
        if self.dimension:
            self.is_array = True
        else:
            self.is_array = False

    def var_specs(self):
        specs = [self.dtype.type_spec()]
        if self.dimension:
            specs.append('dimension(%s)' % ', '.join(self.dimension))
        return specs

    def declaration(self):
        return '%s :: %s' % (', '.join(self.var_specs()), self.name)


class Argument(object):

    def __init__(self, name, dtype,
                 intent=None,
                 dimension=None,
                 value=None,
                 is_return_arg=False):
        self._var = Var(name=name, dtype=dtype, dimension=dimension)
        self.intent = intent
        self.value = value
        self.is_return_arg = is_return_arg

    def _get_name(self):
        return self._var.name
    name = property(_get_name)

    def _get_dtype(self):
        return self._var.dtype
    dtype = property(_get_dtype)

    def _get_dimension(self):
        return self._var.dimension
    dimension = property(_get_dimension)

    def _get_ktp(self):
        return self._var.dtype.ktp
    ktp = property(_get_ktp)

    def _is_array(self):
        return self._var.is_array
    is_array = property(_is_array)

    def declaration(self):
        var = self._var
        specs = var.var_specs()
        if self.intent and not self.is_return_arg:
            if self.intent != 'hide':
                specs.append('intent(%s)' % self.intent)
        return '%s :: %s' % (', '.join(specs), self.name)

    def c_declaration(self):
        return "%s *%s" % (self.ktp, self.name)

class ProcArgument(object):
    def __init__(self, proc):
        self.proc = proc
        self.name = proc.name

class ArgManager(object):
    
    def __init__(self, args, return_arg=None):
        self._args = args
        self._return_arg = return_arg

    def extern_arg_list(self):
        ret = []
        for arg in self._args:
            ret.append(arg.name)
        return ret

    def order_declarations(self):
        decl_list = []
        undeclared = self._args[:]
        while undeclared:
            for arg in undeclared[:]:
                if not arg.is_array:
                    decl_list.append(arg)
                    undeclared.remove(arg)
                else:
                    shape_declared = True
                    undecl_names = [_arg.name for _arg in undeclared]
                    for ext_name in arg.dimension:
                        if ext_name in undecl_names:
                            shape_declared = False
                            break
                    if shape_declared:
                        decl_list.append(arg)
                        undeclared.remove(arg)
        assert not undeclared
        assert len(decl_list) == len(self._args)
        return decl_list

    def arg_declarations(self):
        decls = []
        for arg in self.order_declarations():
            decls.append(arg.declaration())
        if self._return_arg:
            decls.append(self._return_arg.declaration())
        return decls

    def return_var_name(self):
        return self._return_arg.name

    def all_dtypes(self):
        dts = []
        for arg in self._args:
            dts.append(arg.dtype)
        if self._return_arg:
            dts.append(self._return_arg.dtype)
        return dts

class Procedure(object):

    def __init__(self, name, args):
        super(Procedure, self).__init__()
        if not valid_fort_name(name):
            raise InvalidNameException("%s is not a valid Fortran procedure name.")
        self.name = name
        self.args = args
        self.arg_man = None

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def proc_declaration(self):
        return "%s %s(%s)" % (self.kind, self.name, ', '.join(self.extern_arg_list()))

    def proc_preamble(self, ktp_mod, buf):
        buf.putln('use %s' % ktp_mod)
        buf.putln('implicit none')
        for decl in self.arg_declarations():
            buf.putln(decl)

    def proc_end(self):
        return "end %s %s" % (self.kind, self.name)

    def all_dtypes(self):
        return self.arg_man.all_dtypes()

class Function(Procedure):
    
    def __init__(self, name, args, return_type):
        super(Function, self).__init__(name, args)
        self.return_arg = Argument(name=name, dtype=return_type, intent='out', is_return_arg=True)
        self.kind = 'function'
        self.arg_man = ArgManager(self.args, self.return_arg)

class Subroutine(Procedure):

    def __init__(self, name, args):
        super(Subroutine, self).__init__(name, args)
        self.kind = 'subroutine'
        self.arg_man = ArgManager(self.args)

class Module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class Use(object):

    def __init__(self, mod, only=None):
        pass
