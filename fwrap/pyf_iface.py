#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import fort_expr
from intrinsics import intrinsics
import re
from configuration import default_cfg
from fwrap.astnode import AstNode

vfn_re = re.compile(r'[a-zA-Z][_a-zA-Z0-9]{,62}$')
vfn_matcher = vfn_re.match
def valid_fort_name(name):
    return vfn_matcher(name)

def _py_kw_mangler(name):
    # mangles name if it is reserved in some way
    kwds = (
        # Python keywords
        'and', 'del', 'from', 'not', 'while', 'as', 'elif', 'global', 'or',
        'with', 'assert', 'else', 'if', 'pass', 'yield', 'break', 'except',
        'import', 'print', 'class', 'exec', 'in', 'raise', 'continue',
        'finally', 'is', 'return', 'def', 'for', 'lambda', 'try',
        # Cython keywords
        'include', 'ctypedef', 'cdef', 'cpdef',
        'cimport', 'by',
        # We always cimport numpy as np
        'np'
        )
    if name.lower() in kwds:
        return "%s__" % name
    return name

def py_kw_mangle_expression(expr):
    # mangles every keyword found in expression
    def match_action(match):
        return _py_kw_mangler(match.group(0))
    return vfn_re.sub(match_action, expr)

class InvalidNameException(Exception):
    pass

class ScalarIntExpr(object):

    _find_names = re.compile(r'(?<![_\d])[a-z][a-z0-9_%]*', re.IGNORECASE).findall

    def __init__(self, expr_str):
        self.expr_str = expr_str.lower()
        self._expr = fort_expr.parse(self.expr_str)
        xtor = fort_expr.ExtractNames()
        xtor.visit(self._expr)
        self.funcnames = set(xtor.funcnames)
        self.names = set(xtor.names).union(self.funcnames)


class Dtype(object):

    cdef_extern_decls = ''

    cimport_decls = ''

    def __init__(self, fw_ktp, mangler, lang='fortran',
                 length=None, kind=None,
                 cname=None):

        if not valid_fort_name(fw_ktp):
            raise InvalidNameException(
                    "%s is not a valid fortran parameter name." % fw_ktp)

        self.fw_ktp = fw_ktp
        if not fw_ktp.endswith("_t"):
            self.fw_ktp = "%s_t" % self.fw_ktp
        if mangler is None:
            self.fw_ktp = self.mangler % self.fw_ktp

        self.length = length
        if self.length is not None:
            self.length = str(self.length)

        self.kind = kind
        if self.kind is not None:
            self.kind = str(self.kind)

        self.type = None
        self.lang = lang

        #XXX: refactor this with lang
        self.cname = cname
        self.npy_enum = "%s_enum" % self.fw_ktp

    def _get_odecl(self):

        #XXX: refactor this; new attribute?
        if self.lang == 'c' and self.cname:
            return self.cname

        if self.length and self.kind:
            raise ValueError(
                    "both length and kind given for datatype %s" % self.type)

        if self.length:
            return "%s*%s" % (self.type, self.length)
        elif self.kind == 'kind(0)':
            return self.type
        elif self.kind:
            return "%s(kind=%s)" % (self.type, self.kind)
        else:
            return None
    odecl = property(_get_odecl)

    def __hash__(self):
        return hash(self.fw_ktp + (self.odecl or '') + self.type)

    def __eq__(self, other):
        return (isinstance(other, Dtype) and
                self.fw_ktp == other.fw_ktp and
                self.odecl == other.odecl and
                self.type == other.type)

    def __ne__(self, other):
        return not self == other
                
    def type_spec(self):
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

    def depends(self):
        if not self.odecl:
            return set()
        else:
            return ScalarIntExpr(self.odecl).names - intrinsics

    def py_type_name(self):
        from fwrap.gen_config import py_type_name_from_type
        return py_type_name_from_type(self.fw_ktp)

    def __repr__(self):
        return '<Dtype: %s>' % self.type_spec()


class CharacterType(Dtype):

    cdef_extern_decls = '''\
cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)
'''

    mangler = "fw_%s"

    def __init__(self, fw_ktp, len, mangler=None, kind=None, **kwargs):
        super(CharacterType, self).__init__(fw_ktp,
                                    mangler=mangler,
                                    length=len, kind=kind,
                                    **kwargs)
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

    def _get_odecl(self):

        sel = []
        if self.length:
            sel.append("len=%s" % self.length)
        if self.kind:
            sel.append("kind=%s" % self.kind)

        if sel:
            return "%s(%s)" % (self.type, ', '.join(sel))
        else:
            return self.type

    odecl = property(_get_odecl)


default_character = CharacterType(
        fw_ktp="character", len='1', kind="kind('a')")


class IntegerType(Dtype):

    mangler = "fwi_%s"

    def __init__(self, fw_ktp, mangler=None, **kwargs):
        super(IntegerType, self).__init__(fw_ktp, mangler=mangler, **kwargs)
        self.type = 'integer'


default_integer = IntegerType(
        fw_ktp='integer', kind="kind(0)")

class DimType(Dtype):
    
    def __init__(self):
        super(DimType, self).__init__('fw_shape', mangler='%s',
                                      cname='npy_intp', lang='c')
        self.type = 'integer'

    def orig_type_spec(self):
        # There isn't an odecl in Fortran. It is requested in f77binding mode.
        # For now, use the default integer; with some build system improvements
        # one may be able to use integer*4 or integer*8 instead.

        # Note that the odecl (the cname) is left as npy_intp
        return 'integer'

dim_dtype = DimType()#IntegerType(fw_ktp="npy_intp", cname="npy_intp", lang='c')


class LogicalType(Dtype):

    mangler = "fwl_%s"

    def __init__(self, fw_ktp, mangler=None, **kwargs):
        super(LogicalType, self).__init__(fw_ktp, mangler=mangler, **kwargs)
        self.type = 'logical'

    # FIXME: get rid of this when logical arrays use c_f_pointer.
    # FIXME: currently this is a workaround for 4.3.3 <= gfortran version <
    # 4.4.
    def _get_odecl(self):

        #XXX: refactor this; new attribute?
        if self.lang == 'c' and self.cname:
            return self.cname

        if self.length and self.kind:
            raise ValueError(
                    "both length and kind given for datatype %s" % self.type)

        if self.length:
            return "%s*%s" % ('integer', self.length)
        elif self.kind:
            return "%s(kind=%s)" % ('integer', self.kind)
        else:
            return None
    odecl = property(_get_odecl)

default_logical = LogicalType(
        fw_ktp='logical', kind="kind(0)")


class RealType(Dtype):

    mangler = "fwr_%s"

    def __init__(self, fw_ktp, mangler=None, **kwargs):
        super(RealType, self).__init__(fw_ktp, mangler=mangler, **kwargs)
        self.type = 'real'

default_real = RealType(fw_ktp='real', kind="kind(0.0)")
default_dbl  = RealType(fw_ktp='dbl', kind="kind(0.0D0)")


class ComplexType(Dtype):

    mangler = "fwc_%s"

    def __init__(self, fw_ktp, mangler=None, **kwargs):
        super(ComplexType, self).__init__(fw_ktp, mangler=mangler, **kwargs)
        self.type = 'complex'


default_complex = ComplexType(
        fw_ktp='complex', kind="kind((0.0,0.0))")
default_double_complex = ComplexType(
        fw_ktp='dbl_complex', kind="kind((0.0D0,0.0D0))")

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

class _NamedType(object):
    '''
    Abstractish base class for something with a name & a type,
    including Parameters, Vars and Arguments.
    '''

    def __init__(self, name, dtype, dimension=None):
        if not valid_fort_name(name):
            raise InvalidNameException(
                    "%s is not a valid fortran variable name.")
        self.name = name.lower()
        self.dtype = dtype
        if dimension:
            self.dimension = Dimension(dimension)
        else:
            self.dimension = None
        self.is_array = bool(self.dimension)

    def var_specs(self, orig=False):
        if orig:
            specs = [self.dtype.orig_type_spec()]
        else:
            specs = [self.dtype.type_spec()]
        if self.dimension:
            specs.append(self.dimension.attrspec)
        return specs

    def declaration(self, cfg):
        orig = cfg.fc_wrapper_orig_types
        return '%s :: %s' % ( ', '.join(self.var_specs(orig)), self.name)

    def c_type(self):
        return self.dtype.c_declaration()

    def c_declaration(self):
        return "%s%s" % (self.dtype.c_declaration(), self.name)

    def depends(self):
        deps = self.dtype.depends()
        if self.is_array:
            deps = deps.union(self.dimension.depnames)
        return deps - intrinsics

class Parameter(_NamedType):

    def __init__(self, name, dtype, expr, dimension=None):
        super(Parameter, self).__init__(name, dtype, dimension)
        self.expr = ScalarIntExpr(expr)
        self.depnames = self.expr.names

    def var_specs(self, orig=False):
        specs = super(Parameter, self).var_specs(orig)
        specs.append('parameter')
        return specs

    def depends(self):
        deps = super(Parameter, self).depends()
        return deps.union(self.expr.names) - intrinsics

    def declaration(self, cfg):
        decl = super(Parameter, self).declaration(cfg)
        return "%s = %s" % (decl, self.expr.expr_str)

class Dim(object):

    def __init__(self, spec):
        if isinstance(spec, basestring):
            spec = tuple(spec.split(':'))
        self.spec = tuple([ScalarIntExpr(s) for s in spec])

        self.is_assumed_shape = False
        self.is_assumed_size = False
        self.is_explicit_shape = False

        if len(self.spec) == 2:
            lbound, ubound = [sp.expr_str for sp in self.spec]
            if ubound and not lbound:
                raise ValueError(
                        "%r is an invalid dimension spec" % self.dim_spec_str())
            if ubound == '*':
                self.is_assumed_size = True
            elif ubound:
                self.is_explicit_shape = True
            else:
                self.is_assumed_shape = True

        elif len(self.spec) == 1:
            if self.spec[0].expr_str == '*':
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
            self.sizeexpr = None
        elif self.is_assumed_shape:
            self.sizeexpr = None
        elif len(self.spec) == 2:
            self.sizeexpr = ("((%s) - (%s) + 1)" %
                    tuple(reversed([sp.expr_str for sp in self.spec])))
        elif len(self.spec) == 1:
            self.sizeexpr = "(%s)" % self.spec[0].expr_str

        self._set_depnames()

    def _set_depnames(self):
        self.depnames = set()
        for sie in self.spec:
            self.depnames.update(sie.names)

    def dim_spec_str(self):
        return ":".join([sp.expr_str for sp in self.spec])

    def __eq__(self, other):
        return (self.is_assumed_shape == other.is_assumed_shape and
                self.is_assumed_size == other.is_assumed_size and
                self.is_explicit_shape == other.is_explicit_shape and
                self.sizeexpr == other.sizeexpr)

    def __ne__(self, other):
        return not self == other
                
    def __repr__(self):
        return '<Dim: %s>' % self.sizeexpr

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

    def __eq__(self, other):
        if not isinstance(other, Dimension):
            return False
        return self.dims == other.dims

    def __ne__(self, other):
        return not self == other
                
    def __len__(self):
        return len(self.dims)

    def __iter__(self):
        return iter(self.dims)

    def __repr__(self):
        return '<Dimension: %s>' % repr(self.dims)


class Var(_NamedType):

    def __init__(self, name, dtype, dimension=None, isptr=False):
        super(Var, self).__init__(name, dtype, dimension)
        self._base = _NamedType(name, dtype, dimension)
        self.isptr = isptr

    def var_specs(self, orig=False):
        specs = super(Var, self).var_specs(orig)
        if self.isptr:
            specs.append('pointer')
        return specs

class Argument(AstNode):
    name = None
    dtype = None
    intent = None
    isvalue = None
    is_return_arg = False
    init_code = None
    hide_in_wrapper = False
    check = ()
    dimension = None

    def _update(self):
        self._var = Var(name=self.name, dtype=self.dtype,
                        dimension=self.dimension)
        if self.dtype.type == 'c_ptr' and not self.isvalue:
            raise ValueError(
                "argument '%s' has datatype 'type(c_ptr)' "
                "but does not have the 'value' attribute." % self.name)

    def _get_ktp(self):
        return self._var.dtype.fw_ktp
    ktp = property(_get_ktp)

    def _is_array(self):
        return self._var.is_array
    is_array = property(_is_array)

    def declaration(self, cfg=default_cfg):
        orig = cfg.fc_wrapper_orig_types
        var = self._var
        specs = var.var_specs(orig=orig)
        if self.isvalue:
            assert not cfg.f77binding
            specs.append('value')
        if not cfg.f77binding:
            specs.extend(self.intent_spec())
        return '%s :: %s' % (', '.join(specs), self.name)

    def intent_spec(self):
        if self.intent and not self.is_return_arg:
            return ['intent(%s)' % self.intent]
        return []

    def c_type(self):
        return self._var.c_type()

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

class ArgManager(object):

    def __init__(self, args, return_arg=None, params=()):
        self._args = list(args)
        self._return_arg = return_arg
        self._params = list(params)
        self._trim_params()
        self._check_namespace()

    def _trim_params(self):
        # remove params that aren't necessary as part of an argument
        # declaration.

        pnames = set([p.name for p in self._params])
        name2o = dict([(o.name, o) for o in (self._args + self._params)])
        queue = set(self._args[:])
        while queue:
            o = queue.pop()
            for depname in o.depends():
                dep = name2o[depname]
                if depname in name2o:
                    # Make sure we get all dependencies in the tree.
                    queue.add(dep)
                if depname in pnames:
                    # The parameter is required as part of an argument
                    # declaration, so remove it from pnames.
                    pnames.remove(depname)

        # Whatever is left in pnames is not required for an argument
        # declaration; remove it from self._params
        for pname in pnames:
            self._params.remove(name2o[pname])

    def extern_arg_list(self):
        ret = []
        for arg in self._args:
            ret.append(arg.name)
        return ret

    def _provided_names(self):
        provided_names = set()
        for o in (self._args + self._params):
            provided_names.add(o.name)
        return provided_names.union(intrinsics)

    def _required_names(self):
        req_names = set()
        for o in (self._args + self._params):
            req_names.update(o.depends())
        return req_names

    def _check_namespace(self):
        provided_names = self._provided_names()
        required_names = self._required_names()

        left_out = required_names - provided_names

        if left_out:
            raise RuntimeError(
                    "Required names not provided by scope %r" % list(left_out))

    def order_declarations(self):
        decl_list = []
        decl_set = set()
        undeclared = list(self._args) + list(self._params)
        while undeclared:
            undecl_cpy = undeclared[:]
            for arg in undecl_cpy:
                deps = arg.depends()
                if not deps or deps <= decl_set.union(intrinsics):
                    decl_list.append(arg)
                    decl_set.add(arg.name)
                    undeclared.remove(arg)
            assert len(undecl_cpy) > len(undeclared)
        assert not undeclared
        assert len(decl_list) == len(self._args) + len(self._params)
        return decl_list

    def arg_declarations(self, cfg=default_cfg):
        decls = []
        od = self.order_declarations()
        for arg in od:
            decls.append(arg.declaration(cfg))
        if self._return_arg:
            decls.append(self._return_arg.declaration(cfg))
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


class Procedure(AstNode):
    name = None
    args = ()
    arg_man = None
    params = ()
    language = 'fortran'
    kind = None

    def _validate(self, name, language, **kw):
        assert language in ('fortran', 'pyf')
        if not valid_fort_name(name):
            raise InvalidNameException(
                    "%s is not a valid Fortran procedure name.")
        
    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self, cfg=default_cfg):
        return self.arg_man.arg_declarations(cfg)

    def proc_declaration(self, cfg):
        return ("%s %s(%s)" %
                (self.kind, self.name, ', '.join(self.extern_arg_list())))

    def proc_preamble(self, ktp_mod, buf, cfg):
        if not cfg.f77binding:
            buf.putln('use %s' % ktp_mod)
        buf.putln('implicit none')
        for decl in self.arg_declarations(cfg):
            buf.putln(decl)

    def proc_end(self):
        return "end %s %s" % (self.kind, self.name)

    def all_dtypes(self):
        return self.arg_man.all_dtypes()


class Function(Procedure):
    kind = 'function'

    def _update(self):
        self.return_arg.name = self.name # TODO: Refactor
        self.arg_man = ArgManager(args=self.args,
                            return_arg=self.return_arg,
                            params=self.params)

class Subroutine(Procedure):
    kind = 'subroutine'

    def _update(self):
        self.arg_man = ArgManager(self.args, params=self.params)


class Module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass


class Use(object):

    def __init__(self, mod, only=None):
        pass

#
# Check
#

class UnsupportedInputError(Exception):
    pass

def check_tree(procs, cfg):
    if cfg.f77binding:
        check_tree_f77binding(procs, cfg)

def check_tree_f77binding(procs, cfg):
    for proc in procs:
        for arg in proc.args:
            if arg.dimension:
                for dim in arg.dimension.dims:
                    if dim.is_assumed_shape:
                        raise UnsupportedInputError(
                            'assumed shape arrays not supported '
                            'in f77binding mode')
