#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import pyf_iface
from fwrap import constants
from fwrap.code import CodeBuffer
from fwrap.pyf_iface import _py_kw_mangler, py_kw_mangle_expression
from fwrap.pyf_utils import c_to_cython

import re
import warnings

plain_sizeexpr_re = re.compile(r'\(([a-zA-Z0-9_]+)\)')

class CythonCodeGenerationContext:
    def __init__(self, cfg):
        from fwrap.configuration import Configuration
        assert isinstance(cfg, Configuration)
        self.utility_codes = set()
        self.language = None
        self.cfg = cfg

    def use_utility_code(self, snippet):
        self.utility_codes.add(snippet)

def wrap_fc(ast):
    ret = []
    for proc in ast:
        ret.append(ProcWrapper(wrapped=proc))
    return ret

def generate_cy_pxd(ast, fc_pxd_name, buf):
    buf.putln('cimport numpy as np')
    buf.putln("from %s cimport *" % fc_pxd_name)
    buf.putln('')
    for proc in ast:
        buf.putln(proc.cy_prototype())

def gen_cimport_decls(buf):
    for dtype in pyf_iface.intrinsic_types:
        buf.putlines(dtype.cimport_decls)

def gen_cdef_extern_decls(buf):
    for dtype in pyf_iface.intrinsic_types:
        buf.putlines(dtype.cdef_extern_decls)

def generate_cy_pyx(ast, name, buf, cfg):
    from fwrap.deduplicator import cy_deduplify
    ctx = CythonCodeGenerationContext(cfg)
    if cfg.detect_templates:
        ast = cy_deduplify(ast, cfg)    
    buf.putln("#cython: ccomplex=True")
    buf.putln('')
    buf.putln('# Fwrap configuration:')
    cfg.serialize_to_pyx(buf)
    buf.putln(' ')
    put_cymod_docstring(ast, name, buf)
    buf.putln("np.import_array()")
    buf.putln("include 'fwrap_ktp.pxi'")
    gen_cimport_decls(buf)
    gen_cdef_extern_decls(buf)
    for proc in ast:
        ctx.language = proc.wrapped.wrapped.language
        assert ctx.language in ('fortran', 'pyf')
        proc.generate_wrapper(ctx, buf)
    for utilcode in ctx.utility_codes:
        buf.putblock(utilcode)

def put_cymod_docstring(ast, modname, buf):
    dstring = get_cymod_docstring(ast, modname)
    buf.putln('"""')
    buf.putlines(dstring)
    buf.putempty()
    buf.putln('"""')

# XXX:  Put this in a cymodule class?
def get_cymod_docstring(ast, modname):
    from fwrap.version import get_version
    from fwrap.gen_config import all_dtypes
    dstring = ("""\
The %s module was generated with Fwrap v%s.

Below is a listing of functions and data types.
For usage information see the function docstrings.

""" % (modname, get_version())).splitlines()
    dstring += ["Functions",
                "---------"]
    # Functions
    names = []
    for proc in ast:
        names.extend(proc.get_names())
    names.sort()
    names = ["%s(...)" % name for name in names]
    dstring += names

    dstring += [""]

    dstring += ["Data Types",
                "----------"]
    # Datatypes
    dts = all_dtypes(ast)
    names = sorted([dt.py_type_name() for dt in dts])
    dstring += names

    return dstring

def CyArgWrapper(arg):
    import fc_wrap
    if isinstance(arg, fc_wrap.FcErrStrArg):
        return _CyErrStrArg(arg)
    elif isinstance(arg.dtype, pyf_iface.ComplexType):
        return _CyCmplxArg(arg)
    elif isinstance(arg.dtype, pyf_iface.CharacterType):
        return _CyCharArg(arg)
    return _CyArgWrapper(arg)

class _CyArgWrapperBase(object):
    def equal_up_to_type(self, other_arg):
        return self.arg.equal_up_to_type(other_arg.arg)    

class _CyArgWrapper(_CyArgWrapperBase):

    is_array = False

    def __init__(self, arg):
        self.arg = arg
        self.name = _py_kw_mangler(self.arg.name)
        self.intern_name = self.name
        self.cy_dtype_name = self._get_cy_dtype_name()
        self.hide_in_wrapper = arg.hide_in_wrapper

    def _get_cy_dtype_name(self):
        return self.arg.ktp

    def _get_py_dtype_name(self):
        from fwrap.gen_config import py_type_name_from_type
        return py_type_name_from_type(self.cy_dtype_name)

    def extern_declarations(self):
        """
        Returns a list [(decl, default)] of argument declarations
        needed. "decl" is the declaration string and default is a
        string representation of possible default value (normally
        either None or 'None')
        """
        if (self.arg.intent in ('in', 'inout', None) and
            not self.hide_in_wrapper):
            # In pyf files, one can insert initialization code using '= value'
            # in the declaration. For now, put it here (that is, only supports
            # literals and not expressions in the other arguments)
            return [("%s %s" % (self.cy_dtype_name, self.name), self.arg.init_code)]
        return []

    def docstring_extern_arg_list(self):
        if (self.arg.intent in ("in", "inout", None) and
            not self.hide_in_wrapper):
            return [self.name]
        return []

    def intern_declarations(self, ctx):
        if self.arg.intent == 'out' or self.hide_in_wrapper:
            return ["cdef %s %s" % (self.cy_dtype_name, self.name)]
        return []

    def call_arg_list(self, ctx):
        return ["&%s" % self.name]

    def post_call_code(self, ctx):
        return []

    def pre_call_code(self, ctx):
        # When parsing pyf files, one can specify arbitrary initialization
        # code (assumed to be in Cython). For hidden arguments, this
        # must be inserted here.
        lines = []
        if self.hide_in_wrapper and self.arg.init_code is not None:
            lines.append("%s = %s" % (self.name, self.arg.init_code))
        for c in self.arg.check:
            c = py_kw_mangle_expression(c)
            c = c_to_cython(c)
            lines.append("if not (%s):" % c)
            lines.append("    raise ValueError('Condition on arguments not satisfied: %s')" % c)
        return lines

    def return_tuple_list(self):
        if self.name == constants.ERR_NAME:
            return []
        elif self.arg.intent in ('out', 'inout', None):
            return [self.name]
        return []

    docstring_return_tuple_list = return_tuple_list

    def _gen_dstring(self):
        dstring = ("%s : %s" %
                    (self.name, self._get_py_dtype_name()))
        if self.arg.intent is not None:
            dstring += ", intent %s" % (self.arg.intent)
        return [dstring]

    def in_dstring(self):
        if self.arg.intent not in ('in', 'inout', None):
            return []
        return self._gen_dstring()

    def out_dstring(self):
        if self.name == constants.ERR_NAME:
            return []
        if self.arg.intent not in ('out', 'inout', None):
            return []
        return self._gen_dstring()

class _CyCharArg(_CyArgWrapper):

    def __init__(self, arg):
        super(_CyCharArg, self).__init__(arg)
        self.intern_name = 'fw_%s' % self.name
        self.intern_len_name = '%s_len' % self.intern_name
        self.intern_buf_name = '%s_buf' % self.intern_name

    def _get_cy_dtype_name(self):
        return "fw_bytes"

    def _get_py_dtype_name(self):
        from fwrap.gen_config import py_type_name_from_type
        return py_type_name_from_type(self.arg.ktp)

    def extern_declarations(self):
        if self.arg.intent in ('in', 'inout', None):
            return [("%s %s" % (self.cy_dtype_name, self.name), None)]
        elif self.is_assumed_size():
            return [('%s %s' % (self.cy_dtype_name, self.name), None)]
        return []

    def intern_declarations(self, ctx):
        ret = ['cdef %s %s' % (self.cy_dtype_name, self.intern_name),
                'cdef fw_shape_t %s' % self.intern_len_name]
        if self.arg.intent in ('out', 'inout', None):
            ret.append('cdef char *%s' % self.intern_buf_name)
        return ret

    def get_len(self):
        return self.arg.dtype.len

    def is_assumed_size(self):
        return self.get_len() == '*'

    def _len_str(self):
        if self.is_assumed_size():
            len_str = 'len(%s)' % self.name
        else:
            len_str = self.get_len()
        return len_str

    def _in_pre_call_code(self):
        return ['%s = len(%s)' % (self.intern_len_name, self.name),
                '%s = %s' % (self.intern_name, self.name)]

    def _out_pre_call_code(self):
        len_str = self._len_str()
        return ['%s = %s' % (self.intern_len_name, len_str),
               self._fromstringandsize_call(),
               '%s = <char*>%s' % (self.intern_buf_name, self.intern_name),]

    def _inout_pre_call_code(self):
       ret = self._out_pre_call_code()
       ret += ['memcpy(%s, <char*>%s, %s+1)' %
               (self.intern_buf_name, self.name, self.intern_len_name)]
       return ret

    def pre_call_code(self, ctx):
        if self.arg.intent == 'in':
            return self._in_pre_call_code()
        elif self.arg.intent == 'out':
            return self._out_pre_call_code()
        elif self.arg.intent in ('inout', None):
            return self._inout_pre_call_code()

    def _fromstringandsize_call(self):
        return '%s = PyBytes_FromStringAndSize(NULL, %s)' % \
                    (self.intern_name, self.intern_len_name)

    def call_arg_list(self, ctx):
        if self.arg.intent == 'in':
            return ['&%s' % self.intern_len_name,
                    '<char*>%s' % self.intern_name]
        else:
            return ['&%s' % self.intern_len_name, self.intern_buf_name]

    def return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.intern_name]
        return []

    def _gen_dstring(self):
        dstring = ["%s : %s" %
                    (self.name, self._get_py_dtype_name())]
        dstring.append("len %s" % self.get_len())
        if self.arg.intent is not None:
            dstring.append("intent %s" % (self.arg.intent))
        return [", ".join(dstring)]

    def in_dstring(self):
        if self.is_assumed_size():
            return self._gen_dstring()
        else:
            return super(_CyCharArg, self).in_dstring()


class _CyErrStrArg(_CyArgWrapperBase):
    hide_in_wrapper = False

    def __init__(self, arg):
        self.arg = arg
        self.name = _py_kw_mangler(self.arg.name)
        self.intern_name = self.name

    def get_len(self):
        return self.arg.dtype.len

    def extern_declarations(self):
        return []

    def intern_declarations(self, ctx):
        return ['cdef fw_character_t %s[%s]' %
                    (self.name, constants.ERRSTR_LEN)]

    def call_arg_list(self, ctx):
        return [self.name]

    def return_tuple_list(self):
        return []

    def pre_call_code(self, ctx):
        return []

    def post_call_code(self, ctx):
        return []

    def docstring_extern_arg_list(self):
        return []

    def docstring_return_tuple_list(self):
        return []

    def in_dstring(self):
        return []

    def out_dstring(self):
        return []


class _CyCmplxArg(_CyArgWrapper):
    # TODO Is this class needed?
    def __init__(self, arg):
        super(_CyCmplxArg, self).__init__(arg)
        self.intern_name = 'fw_%s' % self.arg.name
        # self.name = self.arg.name

    def intern_declarations(self, ctx):
        return super(_CyCmplxArg, self).intern_declarations(ctx)

    def call_arg_list(self, ctx):
        return ['&%s' % self.name]


def CyArrayArgWrapper(arg):
    if arg.dtype.type == 'character':
        return CyCharArrayArgWrapper(arg)
    return _CyArrayArgWrapper(arg)


class _CyArrayArgWrapper(_CyArgWrapperBase):

    is_array = True
    hide_in_wrapper = False

    def __init__(self, arg):
        from fwrap.gen_config import py_type_name_from_type

        self.arg = arg
        self.extern_name = _py_kw_mangler(self.arg.name)
        self.intern_name = '%s_' % self.extern_name
        self.shape_var_name = '%s_shape_' % self.extern_name

        # In the special case of explicit-shape intent(out) arrays,
        # find the expressions for constructing the output argument
        self.explicit_out_array = (arg.intent == 'out' and
                                   all(dim.is_explicit_shape
                                       for dim in arg.orig_arg.dimension))
        if self.explicit_out_array:
            self.explicit_out_array_sizeexprs = [
                dim.sizeexpr for dim in arg.orig_arg.dimension]
        if arg.hide_in_wrapper:
            raise NotImplementedError()
        # Note: The following are set to something else in
        # deduplicator.TemplatedCyArrayArg
        self.ktp = self.arg.ktp
        self.py_type_name = py_type_name_from_type(self.ktp)
        self.npy_enum = self.arg.dtype.npy_enum

    def extern_declarations(self):
        default_value = 'None' if self.explicit_out_array else None
        return [('object %s' % self.extern_name, default_value)]

    def intern_declarations(self, ctx):
        decls = ["cdef np.ndarray[%s, ndim=%d, mode='fortran'] %s" %
                (self.ktp,
                 self.arg.ndims,
                 self.intern_name,)]
        if ctx.cfg.f77binding:
            decls.append("cdef fw_shape_t %s[%d]" %
                         (self.shape_var_name,
                          self.arg.ndims))
        return decls            

    def _get_py_dtype_name(self):
        return self.py_type_name

    def call_arg_list(self, ctx):
        if not ctx.cfg.f77binding:
            shape_expr = 'np.PyArray_DIMS(%s)' % self.intern_name
        else:
            shape_expr = self.shape_var_name
        return [shape_expr,
                '<%s*>np.PyArray_DATA(%s)' % (self.ktp, self.intern_name)]

    def pre_call_code(self, ctx):
        # NOTE: we can support a STRICT macro that would disable the
        # PyArray_ANYARRAY() call, forcing all incoming arrays to be already F
        # contiguous.
        d = {'intern' : self.intern_name,
             'extern' : self.extern_name,
             'dtenum' : self.npy_enum,
             'ndim' : self.arg.ndims}
        lines = []

        allocate_outs = self.explicit_out_array
        if allocate_outs:
            sizeexprs = list(self.explicit_out_array_sizeexprs)
            if ctx.language != 'pyf':
                # With .pyf, C expressions can be used directly
                # Otherwise, only very simplest cases supported.
                # TODO: Fix this up (compile Fortran-side function to give
                # resulting shape?)
                for i, expr in enumerate(sizeexprs):
                    m = plain_sizeexpr_re.match(expr)
                    if not m:
                        warnings.warn(
                            'Cannot automatically allocate explicit-shape intent(out) array '
                            'as expression is too complicated: %s' % expr)
                        allocate_outs = False
                        break
                    sizeexprs[i] = _py_kw_mangler(m.group(1))
        if not allocate_outs:
            lines.append('%(intern)s = np.PyArray_FROMANY(%(extern)s, %(dtenum)s, '
                         '%(ndim)d, %(ndim)d, np.NPY_F_CONTIGUOUS)' % d)
        else:
            d['shape'] = ', '.join(sizeexprs)
            ctx.use_utility_code(explicit_shape_out_array_utility_code)
            lines.append('%(intern)s = fw_getoutarray(%(extern)s, %(dtenum)s, '
                         '%(ndim)d, [%(shape)s])' % d)

        if ctx.cfg.f77binding:
            ctx.use_utility_code(copy_shape_utility_code)
            lines.append('fw_copyshape(%s, np.PyArray_DIMS(%s), %d)' %
                         (self.shape_var_name, self.intern_name, self.arg.ndims))

        return lines

    def post_call_code(self, ctx):
        return []

    def return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.intern_name]
        return []

    def _gen_dstring(self):
        dims = self.arg.orig_arg.dimension
        ndims = len(dims)
        dstring = ("%s : %s, %dD array, %s" %
                        (self.extern_name,
                         self._get_py_dtype_name(),
                         ndims,
                         dims.attrspec))
        if self.arg.intent is not None:
            dstring += ", intent %s" % (self.arg.intent)
        return [dstring]

    def in_dstring(self):
        return self._gen_dstring()

    def out_dstring(self):
        if self.arg.intent not in ("out", "inout", None):
            return []
        return self._gen_dstring()

    def docstring_extern_arg_list(self):
        return [self.extern_name]

    def docstring_return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.extern_name]
        return []


class CyCharArrayArgWrapper(_CyArrayArgWrapper):

    def __init__(self, arg):
        super(CyCharArrayArgWrapper, self).__init__(arg)
        intern_name = _py_kw_mangler(self.arg.intern_name)
        self.odtype_name = "%s_odtype" % intern_name
        self.shape_name = "%s_shape" % intern_name
        self.name = intern_name

    def intern_declarations(self, ctx):
        ret = super(CyCharArrayArgWrapper, self).intern_declarations(ctx)
        return ret + ["cdef fw_shape_t %s[%d]" %
                (self.shape_name, self.arg.ndims+1)]

    def pre_call_code(self, ctx):
        tmpl = ("%(odtype)s = %(name)s.dtype\n"
                "for i in range(%(ndim)d): "
                    "%(shape)s[i+1] = %(name)s.shape[i]\n"
                "%(name)s.dtype = 'b'\n"
                "%(intern)s = %(name)s\n"
                "%(shape)s[0] = <fw_shape_t>"
                    "(%(name)s.shape[0]/%(shape)s[1])")
        D = {"odtype" : self.odtype_name,
             "ndim" : self.arg.ndims,
             "name" : self.extern_name,
             "intern" : self.intern_name,
             "shape" : self.shape_name}

        return (tmpl  % D).splitlines()

    def post_call_code(self, ctx):
        return ["%s.dtype = %s" % (self.extern_name, self.odtype_name)]

    def call_arg_list(self, ctx):
        shapes = ["&%s[%d]" % (self.shape_name, i)
                    for i in range(self.arg.ndims+1)]
        data = ["<%s*>%s.data" % (self.ktp, self.intern_name)]
        return shapes + data

    def _gen_dstring(self):
        dims = self.arg.orig_arg.dimension
        ndims = len(dims)
        dtype_len = self.arg.dtype.len
        dstring = ["%s : %s" %
                    (self.extern_name, self._get_py_dtype_name())]
        dstring.append("len %s" % dtype_len)
        dstring.append("%dD array" % ndims)
        dstring.append(dims.attrspec)
        if self.arg.intent is not None:
            dstring.append("intent %s" % self.arg.intent)
        return [", ".join(dstring)]


class CyArgWrapperManager(object):

    def __init__(self, args):
        self.args = args

    @classmethod
    def from_fwrapped_proc(cls, fw_proc):
        fw_arg_man = fw_proc.arg_man
        args = []
        for fw_arg in fw_arg_man.arg_wrappers:
            if fw_arg.is_array:
                args.append(CyArrayArgWrapper(fw_arg))
            else:
                args.append(CyArgWrapper(fw_arg))
        return cls(args=args)

    def call_arg_list(self, ctx):
        cal = []
        for arg in self.args:
            cal.extend(arg.call_arg_list(ctx))
        return cal

    def arg_declarations(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.extern_declarations())
        return decls

    def intern_declarations(self, ctx):
        decls = []
        for arg in self.args:
            decls.extend(arg.intern_declarations(ctx))
        return decls

    def return_tuple_list(self):
        rtl = []
        for arg in self.args:
            rtl.extend(arg.return_tuple_list())
        return rtl

    def pre_call_code(self, ctx):
        pcc = []
        for arg in self.args:
            pcc.extend(arg.pre_call_code(ctx))
        return pcc

    def post_call_code(self, ctx):
        pcc = []
        for arg in self.args:
            pcc.extend(arg.post_call_code(ctx))
        return pcc

    def docstring_extern_arg_list(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.docstring_extern_arg_list())
        return decls

    def docstring_return_tuple_list(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.docstring_return_tuple_list())
        return decls

    def docstring_in_descrs(self):
        descrs = []
        for arg in self.args:
            if arg.hide_in_wrapper:
                continue
            descrs.extend(arg.in_dstring())
        return descrs

    def docstring_out_descrs(self):
        descrs = []
        for arg in self.args:
            descrs.extend(arg.out_dstring())
        return descrs

    
class ProcWrapper(object):

    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.unmangled_name = self.wrapped.wrapped_name()
        self.name = _py_kw_mangler(self.unmangled_name)
        self.arg_mgr = CyArgWrapperManager.from_fwrapped_proc(wrapped)
        self.wrapped_name = self.wrapped.name

    def get_names(self):
        # A template proc can provide more than one name
        return [self.name]

    def all_dtypes(self):
        return self.wrapped.all_dtypes()

    def cy_prototype(self, in_pxd=True):
        template = "cpdef api object %(proc_name)s(%(arg_list)s)"
        # Need to use default values only for trailing arguments
        # Currently, no reordering is done, one simply allows
        # trailing arguments that have defaults (explicit-shape,
        # intent(out) arrays)
        arg_decls = self.arg_mgr.arg_declarations()
        if len(arg_decls) > 0:
            types_and_names, defaults = zip(*arg_decls)
            types_and_names = list(types_and_names)
            for i in range(len(defaults) - 1, -1, -1):
                d = defaults[i]
                if d is None:
                    break
                types_and_names[i] = '%s=%s' % (types_and_names[i],
                                                d if not in_pxd else '*')
            arg_list = ', '.join(types_and_names)
        else:
            arg_list = ''
        sdict = dict(proc_name=self.name,
                arg_list=arg_list)
        return template % sdict

    def proc_declaration(self):
        return "%s:" % self.cy_prototype(in_pxd=False)

    def proc_call(self, ctx):
        proc_call = "%(call_name)s(%(call_arg_list)s)" % {
                'call_name' : self.wrapped_name,
                'call_arg_list' : ', '.join(self.arg_mgr.call_arg_list(ctx))}
        return proc_call

    def temp_declarations(self, buf, ctx):
        decls = self.arg_mgr.intern_declarations(ctx)
        for line in decls:
            buf.putln(line)

    def return_tuple(self):
        ret_arg_list = []
        ret_arg_list.extend(self.arg_mgr.return_tuple_list())
        if len(ret_arg_list) > 1:
            return "return (%s,)" % ", ".join(ret_arg_list)
        elif len(ret_arg_list) == 1:
            return "return %s" % ret_arg_list[0]
        else:
            return ''

    def pre_call_code(self, ctx, buf):
        for line in self.arg_mgr.pre_call_code(ctx):
            buf.putln(line)

    def post_call_code(self, ctx, buf):
        for line in self.arg_mgr.post_call_code(ctx):
            buf.putln(line)

    def check_error(self, buf):
        ck_err = ('if fw_iserr__ != FW_NO_ERR__:\n'
                  '    raise RuntimeError(\"an error was encountered '
                           "when calling the '%s' wrapper.\")") % self.name
        buf.putlines(ck_err)

    def post_try_finally(self, ctx, buf):
        post_cc = CodeBuffer()
        self.post_call_code(ctx, post_cc)

        use_try = post_cc.getvalue()

        if use_try:
            buf.putln("try:")
            buf.indent()

        self.check_error(buf)

        if use_try:
            buf.dedent()
            buf.putln("finally:")
            buf.indent()

        buf.putlines(post_cc.getvalue())

        if use_try:
            buf.dedent()

    def generate_wrapper(self, ctx, buf):
        buf.putln(self.proc_declaration())
        buf.indent()
        self.put_docstring(buf)
        self.temp_declarations(buf, ctx)
        self.pre_call_code(ctx, buf)
        buf.putln(self.proc_call(ctx))
        self.post_try_finally(ctx, buf)
        rt = self.return_tuple()
        if rt: buf.putln(rt)
        buf.dedent()

    def put_docstring(self, buf):
        dstring = self.docstring()
        buf.putln('"""')
        buf.putlines(dstring)
        buf.putempty()
        buf.putln('"""')

    def dstring_signature(self):
        in_args = ", ".join(self.arg_mgr.docstring_extern_arg_list())
        dstring = "%s(%s)" % (self.name, in_args)

        doc_ret_vars = self.arg_mgr.docstring_return_tuple_list()
        out_args = ", ".join(doc_ret_vars)
        if len(doc_ret_vars) > 1:
            dstring = '%s -> (%s)' % (dstring, out_args)
        elif len(doc_ret_vars) == 1:
            dstring = '%s -> %s' % (dstring, out_args)

        return [dstring]

    def docstring(self):
        dstring = []
        dstring += self.dstring_signature()
        descrs = self.arg_mgr.docstring_in_descrs()
        dstring += [""]
        dstring += ["Parameters",
                    "----------"]
        if descrs:
            dstring.extend(descrs)
        else:
            dstring += ["None"]
        descrs = self.arg_mgr.docstring_out_descrs()
        if descrs:
            dstring += [""]
            dstring += ["Returns",
                        "-------"]
            dstring.extend(descrs)

        return dstring



explicit_shape_out_array_utility_code = u"""
cdef object fw_getoutarray(object value, int typenum, int ndim, np.intp_t *shape):
    if value is not None:
        return np.PyArray_FROMANY(value, typenum, ndim, ndim, np.NPY_F_CONTIGUOUS)
    else:
        return np.PyArray_ZEROS(ndim, shape, typenum, 1)
"""

copy_shape_utility_code = u"""
cdef void fw_copyshape(fw_shape_t *target, np.intp_t *source, int ndim):
    # In f77binding mode, we do not always have fw_shape_t and np.npy_intp
    # as the same type, so must make a copy
    cdef int i
    for i in range(ndim):
        target[i] = source[i]
"""
