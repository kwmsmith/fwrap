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

    def __init__(self, fw_ktp, odecl=None, lang='fortran', mangler="fwrap_%s"):
        if not valid_fort_name(fw_ktp):
            raise InvalidNameException(
                    "%s is not a valid fortran parameter name." % fw_ktp)
        if mangler:
            self.fw_ktp = mangler % fw_ktp
        else:
            self.fw_ktp = fw_ktp
        self.odecl = odecl
        self.type = None
        self.lang = lang

    def type_spec(self):
        # if len:
            # return '%s(kind=%s, len=%s)' % (self.type, self.fw_ktp, len)
        # else:
            return '%s(kind=%s)' % (self.type, self.fw_ktp)

    def orig_type_spec(self):
        return self.odecl

    def __str__(self):
        return ("%s(fw_ktp=%s, odecl=%s)" %
                (type(self), self.fw_ktp, self.odecl))

    def all_dtypes(self):
        return [self]

    def c_declaration(self):
        return "%s *" % self.fw_ktp


class CharacterType(Dtype):

    cdef_extern_decls = '''\
cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)
'''

    def __init__(self, fw_ktp, len, odecl=None, **kwargs):
        super(CharacterType, self).__init__(fw_ktp, odecl, **kwargs)
        self.len = str(len)
        self.type = 'character'

    def all_dtypes(self):
        adts = super(CharacterType, self).all_dtypes()
        return adts + [dim_dtype, default_character]

    def type_spec(self):
        if self.len:
            return '%s(kind=%s, len=%s)' % (self.type, self.fw_ktp, self.len)
        else:
            return '%s(kind=%s)' % (self.type, self.fw_ktp)


default_character = CharacterType(
        fw_ktp="default_character",
        len='1', odecl="character(kind=kind('a'))")


class IntegerType(Dtype):

    def __init__(self, fw_ktp, odecl=None, lang='fortran', **kwargs):
        super(IntegerType, self).__init__(fw_ktp, odecl, lang, **kwargs)
        self.type = 'integer'


default_integer = IntegerType(
        fw_ktp='default_integer', odecl="integer(kind(0))")

dim_dtype = IntegerType(fw_ktp="npy_intp", odecl='npy_intp', lang='c')


class LogicalType(Dtype):

    def __init__(self, fw_ktp, odecl=None, **kwargs):
        super(LogicalType, self).__init__(fw_ktp, odecl, **kwargs)
        self.type = 'logical'
        if self.odecl:
            self.odecl = self.odecl.replace('logical', 'integer')


default_logical = LogicalType(
        fw_ktp='default_logical', odecl="integer(kind=kind(0))")


class RealType(Dtype):

    def __init__(self, fw_ktp, odecl=None, **kwargs):
        super(RealType, self).__init__(fw_ktp, odecl, **kwargs)
        self.type = 'real'


default_real = RealType(fw_ktp='default_real', odecl="real(kind(0.0))")
default_dbl  = RealType(fw_ktp='default_double', odecl="real(kind(0.0D0))")


class ComplexType(Dtype):

    def __init__(self, fw_ktp, odecl=None):
        super(ComplexType, self).__init__(fw_ktp, odecl)
        self.type = 'complex'


default_complex = ComplexType(
        fw_ktp='default_complex', odecl="complex(kind((0.0,0.0)))")
default_double_complex = ComplexType(
        fw_ktp='default_double_complex', odecl="complex(kind((0.0D0,0.0D0)))")

intrinsic_types = [RealType,
                   IntegerType,
                   ComplexType,
                   CharacterType,
                   LogicalType]

class _InternCPtrType(Dtype):
    """
    Not meant to be instantiated beyond the c_ptr_type instance.
    """

    def __init__(self):
        self.type = "c_ptr"

    def type_spec(self):
        return "type(c_ptr)"

    def all_dtypes(self):
        return []

    def c_declaration(self):
        return "void *"

c_ptr_type = _InternCPtrType()

# we delete it from the module so others aren't tempted to instantiate the class.
del _InternCPtrType

class Parameter(object):

    def __init__(self, name, dtype, value):
        self.name = name
        self.dtype = dtype
        self.value = value

class ScalarIntExpr(object):

    _find_names = re.compile(r'[a-z][a-z0-9_%]*', re.IGNORECASE).findall

    def __init__(self, expr):
        self.expr = expr.lower()

    def find_names(self):
        depnames = [s.split('%',1)[0] for s in self._find_names(self.expr)]
        return set(depnames)

class Dim(object):

    def __init__(self, spec):
        if isinstance(spec, basestring):
            spec = tuple(spec.split(':'))
        self.spec = tuple([ScalarIntExpr(s) for s in spec])

        self.is_assumed_shape = False
        self.is_assumed_size = False
        self.is_explicit_shape = False

        if len(self.spec) == 2:
            lbound, ubound = [sp.expr for sp in self.spec]
            if ubound and not lbound:
                raise ValueError(
                        "%r is an invalid dimension spec" % self.dim_spec_str())
            if ubound:
                self.is_explicit_shape = True
            else:
                self.is_assumed_shape = True

        elif len(self.spec) == 1:
            if self.spec[0].expr == '*':
                self.is_assumed_size = True
            else:
                self.is_explicit_shape = True

        if not (self.is_explicit_shape or 
                self.is_assumed_shape or 
                self.is_assumed_size):
            raise ValueError(
                    ("Unable to classify %r dimension spec." %
                        self.dim_spec_str()))

        if self.is_assumed_size:
            self.sizeexpr = "*"
        elif self.is_assumed_shape:
            self.sizeexpr = None
        elif len(self.spec) == 2:
            self.sizeexpr = ("((%s) - (%s) + 1)" %
                    tuple(reversed([sp.expr for sp in self.spec])))
        elif len(self.spec) == 1:
            self.sizeexpr = "(%s)" % self.spec[0].expr

        self._set_depnames()

    def _set_depnames(self):
        self.depnames = set()
        for sie in self.spec:
            names = sie.find_names()
            self.depnames.update(names)

    def dim_spec_str(self):
        return ":".join([sp.expr for sp in self.spec])

class Dimension(object):

    def __init__(self, dims):
        self.dims = []
        for dim in dims:
            if not isinstance(dim, Dim):
                self.dims.append(Dim(dim))
            else:
                self.dims.append(dim)
        self.depnames = set()
        for dim in self.dims:
            self.depnames.update(dim.depnames)
        self._set_attrspec()

    def _set_attrspec(self):
        dimlist = []
        for dim in self.dims:
            dimlist.append(dim.dim_spec_str())
        self.attrspec = "dimension(%s)" % (", ".join(dimlist))

    def __len__(self):
        return len(self.dims)

    def __iter__(self):
        return iter(self.dims)


class Var(object):

    def __init__(self, name, dtype, dimension=None, isptr=False):
        if not valid_fort_name(name):
            raise InvalidNameException(
                    "%s is not a valid fortran variable name.")
        self.name = name
        self.dtype = dtype
        # self.dimension = dimension
        if dimension:
            self.dimension = Dimension(dimension)
        else:
            self.dimension = None
        self.isptr = isptr
        if self.dimension:
            self.is_array = True
        else:
            self.is_array = False

    def var_specs(self, orig=False):
        if orig:
            specs = [self.dtype.orig_type_spec()]
        else:
            specs = [self.dtype.type_spec()]
        if self.dimension:
            specs.append(self.dimension.attrspec)
        if self.isptr:
            specs.append('pointer')
        return specs

    def declaration(self):
        return '%s :: %s' % (', '.join(self.var_specs()), self.name)

    def orig_declaration(self):
        return "%s :: %s" % (', '.join(self.var_specs(orig=True)), self.name)

    def c_declaration(self):
        return "%s%s" % (self.dtype.c_declaration(), self.name)

    def depends(self):
        if not self.is_array:
            return set()
        else:
            return self.dimension.depnames


class Argument(object):

    def __init__(self, name, dtype,
                 intent=None,
                 dimension=None,
                 isvalue=None,
                 is_return_arg=False):
        self._var = Var(name=name, dtype=dtype, dimension=dimension)
        self.intent = intent
        self.isvalue = isvalue
        self.is_return_arg = is_return_arg

        if self.dtype.type == 'c_ptr' and not self.isvalue:
            raise ValueError(
                "argument '%s' has datatype 'type(c_ptr)' "
                "but does not have the 'value' attribute." % self.name)

    def _get_name(self):
        return self._var.name
    def _set_name(self, name):
        self._var.name = name
    name = property(_get_name, _set_name)

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

    def declaration(self, orig=False):
        var = self._var
        specs = var.var_specs(orig=orig)
        if self.isvalue:
            specs.append('value')
        specs.extend(self.intent_spec())
        return '%s :: %s' % (', '.join(specs), self.name)

    def intent_spec(self):
        if self.intent and not self.is_return_arg:
            return ['intent(%s)' % self.intent]
        return []

    def c_declaration(self):
        return self._var.c_declaration()

    def all_dtypes(self):
        adts = self.dtype.all_dtypes()
        if self.is_array:
            adts += [dim_dtype]
        return adts

    def depends(self):
        return self._var.depends()

class HiddenArgument(Argument):

    def __init__(self, name, dtype,
                 value,
                 intent=None,
                 dimension=None,
                 isvalue=None,
                 is_return_arg=False,):
        super(HiddenArgument, self).__init__(name, dtype,
                intent, dimension, isvalue, is_return_arg)
        self.value = value

    def intent_spec(self):
        return []

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
        decl_set = set()
        undeclared = list(self._args)
        while undeclared:
            for arg in undeclared[:]:
                deps = arg.depends()
                if not deps or deps <= decl_set:
                    decl_list.append(arg)
                    decl_set.add(arg.name)
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
            raise InvalidNameException(
                    "%s is not a valid Fortran procedure name.")
        self.name = name
        self.args = args
        self.arg_man = None

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def proc_declaration(self):
        return ("%s %s(%s)" %
                (self.kind, self.name, ', '.join(self.extern_arg_list())))

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

    def __init__(self, name, args, return_arg):
        super(Function, self).__init__(name, args)
        self.return_arg = return_arg
        self.return_arg.name = self.name
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
