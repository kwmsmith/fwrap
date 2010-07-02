import re

vfn_matcher = re.compile(r'[a-zA-Z][_a-zA-Z0-9]{,62}$').match
def valid_fort_name(name):
    return vfn_matcher(name)

class InvalidNameException(Exception):
    pass

# TODO: this should be collected together with the KTP_MOD_NAME constant
def ktp_namer(fw_ktp):
    return "fwrap_%s" % fw_ktp

class Dtype(object):

    cdef_extern_decls = ''

    cimport_decls = ''

    def __hash__(self):
        return hash(self.fw_ktp + (self.odecl or '') + self.type)

    def __eq__(self, other):
        return self.fw_ktp == other.fw_ktp and \
                self.odecl == other.odecl and \
                self.type == other.type

    def __init__(self, fw_ktp, odecl=None, lang='fortran'):
        if not valid_fort_name(fw_ktp):
            raise InvalidNameException("%s is not a valid fortran parameter name." % fw_ktp)
        self.fw_ktp = ktp_namer(fw_ktp)
        self.odecl = odecl
        self.type = None
        self.lang = lang

    def type_spec(self, len=None):
        if len:
            return '%s(kind=%s, len=%s)' % (self.type, self.fw_ktp, len)
        else:
            return '%s(kind=%s)' % (self.type, self.fw_ktp)


    def orig_type_spec(self):
        return self.odecl

    def __str__(self):
        return "%s(fw_ktp=%s, odecl=%s)" % (type(self), self.fw_ktp, self.odecl)

    def all_dtypes(self):
        return [self]


class CharacterType(Dtype):

    cdef_extern_decls = '''\
cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)
'''

    def __init__(self, fw_ktp, len, odecl=None):
        super(CharacterType, self).__init__(fw_ktp, odecl)
        self.len = str(len)
        self.type = 'character'

    def all_dtypes(self):
        adts = super(CharacterType, self).all_dtypes()
        return adts + [dim_dtype]

default_character = CharacterType(fw_ktp="default_character", len='1', odecl="character(kind=kind('a'))")

class IntegerType(Dtype):

    def __init__(self, fw_ktp, odecl=None, lang='fortran'):
        super(IntegerType, self).__init__(fw_ktp, odecl, lang)
        self.type = 'integer'

default_integer = IntegerType(fw_ktp='default_integer', odecl="integer(kind(0))")

dim_dtype = IntegerType(fw_ktp="npy_intp", odecl='npy_intp', lang='c')

class LogicalType(Dtype):

    def __init__(self, fw_ktp, odecl=None):
        super(LogicalType, self).__init__(fw_ktp, odecl)
        self.type = 'integer'
        if self.odecl:
            self.odecl = self.odecl.replace('logical', 'integer')

default_logical = LogicalType(fw_ktp='default_logical', odecl="integer(kind=kind(0))")

class RealType(Dtype):

    def __init__(self, fw_ktp, odecl=None):
        super(RealType, self).__init__(fw_ktp, odecl)
        self.type = 'real'

default_real = RealType(fw_ktp='default_real', odecl="real(kind(0.0))")
default_dbl  = RealType(fw_ktp='default_double', odecl="real(kind(0.0D0))")

class ComplexType(Dtype):

    def __init__(self, fw_ktp, odecl=None):
        super(ComplexType, self).__init__(fw_ktp, odecl)
        self.type = 'complex'

default_complex = ComplexType(fw_ktp='default_complex', odecl="complex(kind((0.0,0.0)))")
default_double_complex = ComplexType(fw_ktp='default_double_complex', odecl="complex(kind((0.0D0,0.0D0)))")

intrinsic_types = [RealType, IntegerType, ComplexType, CharacterType, LogicalType]

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

    def var_specs(self, orig=False, len=None):
        if orig:
            specs = [self.dtype.orig_type_spec()]
        else:
            specs = [self.dtype.type_spec(len)]
        if self.dimension:
            specs.append('dimension(%s)' % ', '.join(self.dimension))
        return specs

    def declaration(self, len=None):
        return '%s :: %s' % (', '.join(self.var_specs(len=len)), self.name)

    def orig_declaration(self):
        return "%s :: %s" % (', '.join(self.var_specs(orig=True)), self.name)


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
        return self._var.dtype.fw_ktp
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

    def all_dtypes(self):
        adts = self.dtype.all_dtypes()
        if self.is_array:
            adts += [dim_dtype]
        return adts

class ProcArgument(object):
    def __init__(self, proc):
        self.proc = proc
        self.name = proc.name

class ArgManager(object):
    
    def __init__(self, args, return_arg=None):
        self._args = list(args)
        self._return_arg = return_arg

    def extern_arg_list(self):
        ret = []
        for arg in self._args:
            ret.append(arg.name)
        return ret

    def order_declarations(self):
        decl_list = []
        undeclared = list(self._args)
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
            dts.extend(arg.all_dtypes())
        if self._return_arg:
            dts.extend(self._return_arg.all_dtypes())
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
