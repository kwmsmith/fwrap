from fwrap import pyf_iface
from fwrap import constants
from fwrap.code import CodeBuffer

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

def generate_cy_pyx(ast, name, buf):
    put_cymod_docstring(ast, name, buf)
    buf.putln("include 'fwrap_ktp.pxi'")
    gen_cimport_decls(buf)
    gen_cdef_extern_decls(buf)
    for proc in ast:
        proc.generate_wrapper(buf)

def put_cymod_docstring(ast, modname, buf):
    dstring = get_cymod_docstring(ast, modname)
    buf.putln('"""')
    buf.putlines(dstring)
    buf.putln('"""')

# XXX:  Put this in a cymodule class?
def get_cymod_docstring(ast, modname):
    from fwrap.version import version
    from fwrap.gen_config import all_dtypes
    dstring = ("""\
The %s module was generated with Fwrap v%s.

Below is a listing of functions and data types.
For usage information see the function docstrings.

""" % (modname, version)).splitlines()
    dstring += ["Functions",
                "---------"]
    # Functions
    for proc in ast:
        dstring += ["%s(...)" % proc.name]

    dstring += [""]

    dstring += ["Data Types",
                "----------"]
    # Datatypes
    dts = all_dtypes(ast)
    for dt in dts:
        dstring += [dt.py_type_name()]

    dstring += [""]

    return dstring

def CyArgWrapper(arg):
    import fc_wrap
    if isinstance(arg, fc_wrap.ErrStrArgWrapper):
        return _CyErrStrArg(arg)
    elif isinstance(arg.dtype, pyf_iface.ComplexType):
        return _CyCmplxArg(arg)
    elif isinstance(arg.dtype, pyf_iface.CharacterType):
        return _CyCharArg(arg)
    return _CyArgWrapper(arg)


class _CyArgWrapper(object):

    is_array = False

    def __init__(self, arg):
        self.arg = arg
        self.intern_name = self.arg.name
        self.name = self.arg.name
        self.cy_dtype_name = self._get_cy_dtype_name()

    def _get_cy_dtype_name(self):
        return self.arg.ktp

    def _get_py_dtype_name(self):
        from fwrap.gen_config import py_type_name_from_type
        return py_type_name_from_type(self.cy_dtype_name)

    def extern_declarations(self):
        if self.arg.intent in ('in', 'inout', None):
            return ["%s %s" % (self.cy_dtype_name, self.arg.name)]
        return []

    def docstring_extern_arg_list(self):
        if self.arg.intent in ("in", "inout", None):
            return [self.arg.name]
        return []

    def intern_declarations(self):
        if self.arg.intent == 'out':
            return ["cdef %s %s" % (self.cy_dtype_name, self.arg.name)]
        return []

    def call_arg_list(self):
        return ["&%s" % self.arg.name]

    def post_call_code(self):
        return []

    def pre_call_code(self):
        return []

    def return_tuple_list(self):
        if self.arg.name == constants.ERR_NAME:
            return []
        elif self.arg.intent in ('out', 'inout', None):
            return [self.arg.name]
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
        if self.arg.name == constants.ERR_NAME:
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
            return ["%s %s" % (self.cy_dtype_name, self.arg.name)]
        elif self.is_assumed_size():
            return ['%s %s' % (self.cy_dtype_name, self.arg.name)]
        return []

    def intern_declarations(self):
        ret = ['cdef %s %s' % (self.cy_dtype_name, self.intern_name),
                'cdef fwi_npy_intp_t %s' % self.intern_len_name]
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

    def pre_call_code(self):
        if self.arg.intent == 'in':
            return self._in_pre_call_code()
        elif self.arg.intent == 'out':
            return self._out_pre_call_code()
        elif self.arg.intent in ('inout', None):
            return self._inout_pre_call_code()

    def _fromstringandsize_call(self):
        return '%s = PyBytes_FromStringAndSize(NULL, %s)' % \
                    (self.intern_name, self.intern_len_name)

    def call_arg_list(self):
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


class _CyErrStrArg(object):

    def __init__(self, arg):
        self.arg = arg
        self.intern_name = self.arg.name
        self.name = self.arg.name

    def get_len(self):
        return self.arg.dtype.len

    def extern_declarations(self):
        return []

    def intern_declarations(self):
        return ['cdef fw_character_t %s[%s]' %
                    (self.name, constants.ERRSTR_LEN)]

    def call_arg_list(self):
        return [self.name]

    def return_tuple_list(self):
        return []

    def pre_call_code(self):
        return []

    def post_call_code(self):
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

    def __init__(self, arg):
        super(_CyCmplxArg, self).__init__(arg)
        self.intern_name = 'fw_%s' % self.arg.name
        self.name = self.arg.name

    def intern_declarations(self):
        return super(_CyCmplxArg, self).intern_declarations()

    def call_arg_list(self):
        return ['&%s' % self.name]


def CyArrayArgWrapper(arg):
    if arg.dtype.type == 'character':
        return CyCharArrayArgWrapper(arg)
    return _CyArrayArgWrapper(arg)


class _CyArrayArgWrapper(object):

    is_array = True

    def __init__(self, arg):
        self.arg = arg
        self.intern_name = '%s_' % self.arg.intern_name

    def extern_declarations(self):
        return ['object %s' % self.arg.intern_name]

    def intern_declarations(self):
        return ["cdef np.ndarray[%s, ndim=%d, mode='fortran'] %s" % \
                (self.arg.ktp,
                 self.arg.ndims,
                 self.intern_name,)
                ]

    def _get_py_dtype_name(self):
        from fwrap.gen_config import py_type_name_from_type
        return py_type_name_from_type(self.arg.ktp)

    def call_arg_list(self):
        shapes = ['<fwi_npy_intp_t*>&%s.shape[%d]' % (self.intern_name, i) \
                                for i in range(self.arg.ndims)]
        data = ['<%s*>%s.data' % (self.arg.ktp, self.intern_name)]
        return shapes + data

    def pre_call_code(self):
        return ["%s = %s" % (self.intern_name, self.arg.intern_name)]

    def post_call_code(self):
        return []

    def return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.intern_name]
        return []

    def _gen_dstring(self):
        dims = self.arg.orig_arg.dimension
        ndims = len(dims)
        dstring = ("%s : %s, %dD array, %s" %
                        (self.arg.name,
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
        return [self.arg.name]

    def docstring_return_tuple_list(self):
        if self.arg.intent in ('out', 'inout', None):
            return [self.arg.name]
        return []


class CyCharArrayArgWrapper(_CyArrayArgWrapper):

    def __init__(self, arg):
        super(CyCharArrayArgWrapper, self).__init__(arg)
        self.odtype_name = "%s_odtype" % self.arg.intern_name
        self.shape_name = "%s_shape" % self.arg.intern_name
        self.name = self.arg.intern_name

    def intern_declarations(self):
        ret = super(CyCharArrayArgWrapper, self).intern_declarations()
        return ret + ["cdef fwi_npy_intp_t %s[%d]" %
                (self.shape_name, self.arg.ndims+1)]

    def pre_call_code(self):
        tmpl = ("%(odtype)s = %(name)s.dtype\n"
                "for i in range(%(ndim)d): "
                    "%(shape)s[i+1] = %(name)s.shape[i]\n"
                "%(name)s.dtype = 'b'\n"
                "%(intern)s = %(name)s\n"
                "%(shape)s[0] = <fwi_npy_intp_t>"
                    "(%(name)s.shape[0]/%(shape)s[1])")
        D = {"odtype" : self.odtype_name,
             "ndim" : self.arg.ndims,
             "name" : self.name,
             "intern" : self.intern_name,
             "shape" : self.shape_name}

        return (tmpl  % D).splitlines()

    def post_call_code(self):
        return ["%s.dtype = %s" % (self.name, self.odtype_name)]

    def call_arg_list(self):
        shapes = ["&%s[%d]" % (self.shape_name, i)
                    for i in range(self.arg.ndims+1)]
        data = ["<%s*>%s.data" % (self.arg.ktp, self.intern_name)]
        return shapes + data

    def _gen_dstring(self):
        dims = self.arg.orig_arg.dimension
        ndims = len(dims)
        dtype_len = self.arg.dtype.len
        dstring = ["%s : %s" %
                    (self.arg.name, self._get_py_dtype_name())]
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

    def call_arg_list(self):
        cal = []
        for arg in self.args:
            cal.extend(arg.call_arg_list())
        return cal

    def arg_declarations(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.extern_declarations())
        return decls

    def intern_declarations(self):
        decls = []
        for arg in self.args:
            decls.extend(arg.intern_declarations())
        return decls

    def return_tuple_list(self):
        rtl = []
        for arg in self.args:
            rtl.extend(arg.return_tuple_list())
        return rtl

    def pre_call_code(self):
        pcc = []
        for arg in self.args:
            pcc.extend(arg.pre_call_code())
        return pcc

    def post_call_code(self):
        pcc = []
        for arg in self.args:
            pcc.extend(arg.post_call_code())
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
        self.name = self.wrapped.wrapped_name()
        self.arg_mgr = CyArgWrapperManager.from_fwrapped_proc(wrapped)

    def all_dtypes(self):
        return self.wrapped.all_dtypes()

    def cy_prototype(self):
        template = "cpdef api object %(proc_name)s(%(arg_list)s)"
        arg_list = ', '.join(self.arg_mgr.arg_declarations())
        sdict = dict(proc_name=self.name,
                arg_list=arg_list)
        return template % sdict

    def proc_declaration(self):
        return "%s:" % self.cy_prototype()

    def proc_call(self):
        proc_call = "%(call_name)s(%(call_arg_list)s)" % {
                'call_name' : self.wrapped.name,
                'call_arg_list' : ', '.join(self.arg_mgr.call_arg_list())}
        return proc_call

    def temp_declarations(self, buf):
        decls = self.arg_mgr.intern_declarations()
        for line in decls:
            buf.putln(line)

    def return_tuple(self):
        ret_arg_list = []
        ret_arg_list.extend(self.arg_mgr.return_tuple_list())
        if ret_arg_list:
            return "return (%s,)" % ", ".join(ret_arg_list)
        else:
            return ''

    def pre_call_code(self, buf):
        for line in self.arg_mgr.pre_call_code():
            buf.putln(line)

    def post_call_code(self, buf):
        for line in self.arg_mgr.post_call_code():
            buf.putln(line)

    def check_error(self, buf):
        ck_err = ('if fw_iserr__ != FW_NO_ERR__:\n'
                  '    raise RuntimeError(\"an error was encountered '
                           "when calling the '%s' wrapper.\")") % self.name
        buf.putlines(ck_err)

    def post_try_finally(self, buf):
        post_cc = CodeBuffer()
        self.post_call_code(post_cc)

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

    def generate_wrapper(self, buf):
        buf.putln(self.proc_declaration())
        buf.indent()
        self.put_docstring(buf)
        self.temp_declarations(buf)
        self.pre_call_code(buf)
        buf.putln(self.proc_call())
        self.post_try_finally(buf)
        rt = self.return_tuple()
        if rt: buf.putln(rt)
        buf.dedent()

    def put_docstring(self, buf):
        dstring = self.docstring()
        buf.putln('"""')
        buf.putlines(dstring)
        buf.putln('"""')

    def docstring(self):
        dstring = []
        in_args = ", ".join(self.arg_mgr.docstring_extern_arg_list())
        out_args = ", ".join(self.arg_mgr.docstring_return_tuple_list())
        dstring += ["%s(%s) -> (%s,)" % (self.name, in_args, out_args)]
        descrs = self.arg_mgr.docstring_in_descrs()
        if descrs:
            dstring += [""]
            dstring += ["Parameters",
                        "----------"]
            dstring.extend(descrs)
        descrs = self.arg_mgr.docstring_out_descrs()
        if descrs:
            dstring += [""]
            dstring += ["Returns",
                        "-------"]
            dstring.extend(descrs)
        dstring += [""]

        return dstring
