from fwrap import pyf_iface as pyf
from fwrap import constants

def _arg_name_mangler(name):
    return "fw_%s" % name

def wrap_pyf_iface(ast):
    fc_wrapper = []
    for proc in ast:
        if proc.kind == 'function':
            fc_wrapper.append(FunctionWrapper(wrapped=proc))
        elif proc.kind == 'subroutine':
            fc_wrapper.append(SubroutineWrapper(wrapped=proc))
        else:
            raise ValueError("object not function or subroutine, %s" % proc)
    return fc_wrapper

def generate_fc_pxd(ast, fc_header_name, buf):
    buf.putln("from %s cimport *" %
                constants.KTP_PXD_HEADER_SRC.split('.')[0])
    buf.putln('')
    buf.putln('cdef extern from "%s":' % fc_header_name)
    buf.indent()
    for proc in ast:
        buf.putln(proc.cy_prototype())
    buf.dedent()

def generate_fc_h(ast, ktp_header_name, buf):
    buf.putln('#include "%s"' % ktp_header_name)
    buf.putln('')
    for proc in ast:
        buf.putln(proc.c_prototype())

def generate_interface(proc, buf, gmn=constants.KTP_MOD_NAME):
        buf.putln('interface')
        buf.indent()
        buf.putln(proc.proc_declaration())
        buf.indent()
        proc.proc_preamble(gmn, buf)
        buf.dedent()
        buf.putln(proc.proc_end())
        buf.dedent()
        buf.putln('end interface')

def _err_test_block(test, errcode, argname):
    tmpl = '''\
if (%(test)s) then
    fw_iserr__ = %(errcode)s
    fw_errstr__ = transfer("%(argname)s", fw_errstr__)
    fw_errstr__(fw_errstr_len) = C_NULL_CHAR
    return
endif
'''
    fs = "%%-%ds" % constants.FORT_MAX_ARG_NAME_LEN
    argname = (fs % argname)[:constants.FORT_MAX_ARG_NAME_LEN]
    if test:
        return (tmpl % locals()).splitlines()
    return []

def _dim_test(dims1, dims2):
    ck = []
    for dim1, dim2 in zip(dims1, dims2):
        if dim1.is_explicit_shape and dim2.is_explicit_shape:
            ck += ['%s .ne. %s' % (dim1.sizeexpr, dim2.sizeexpr)]
    return ' .or. '.join(ck)


class ProcWrapper(object):

    def __init__(self, wrapped):
        self.name = constants.PROC_SUFFIX_TMPL % wrapped.name
        self.wrapped = wrapped
        self.arg_man = None
        self._get_arg_man()

    def _get_arg_man(self):
        self.arg_man = ArgWrapperManager(self.wrapped)

    def wrapped_name(self):
        return self.wrapped.name

    def proc_end(self):
        return "end subroutine %s" % self.name

    def proc_preamble(self, ktp_mod, buf):
        buf.putln('use %s' % ktp_mod)
        buf.putln('implicit none')
        for declaration in (self.arg_declarations() +
                            self.param_declarations()):
            buf.putln(declaration)

    def generate_wrapper(self, buf, gmn=constants.KTP_MOD_NAME):
        buf.putln(self.proc_declaration())
        buf.indent()
        self.proc_preamble(gmn, buf)
        generate_interface(self.wrapped, buf, gmn)
        self.temp_declarations(buf)
        self.pre_call_code(buf)
        self.proc_call(buf)
        self.post_call_code(buf)
        buf.dedent()
        buf.putln(self.proc_end())

    def proc_declaration(self):
        return 'subroutine %s(%s) bind(c, name="%s")' % \
                (self.name, ', '.join(self.extern_arg_list()),
                        self.name)

    def temp_declarations(self, buf):
        for declaration in self.arg_man.temp_declarations():
            buf.putln(declaration)

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def param_declarations(self):
        return self.arg_man.param_declarations()

    def pre_call_code(self, buf):
        for line in self.arg_man.pre_call_code():
            buf.putln(line)

    def post_call_code(self, buf):
        for line in self.arg_man.post_call_code():
            buf.putln(line)

    def proc_call(self, buf):
        proc_call = "%s(%s)" % (self.wrapped.name,
                                ', '.join(self.call_arg_list()))
        if isinstance(self, SubroutineWrapper):
            buf.putln("call %s" % proc_call)
        elif isinstance(self, FunctionWrapper):
            buf.putln("%s = %s" % (self.proc_result_name(), proc_call))

    def call_arg_list(self):
        return self.arg_man.call_arg_list()

    def c_prototype(self):
        return "%s;" % self.cy_prototype()

    def cy_prototype(self):
        args = ", ".join(self.arg_man.c_proto_args())
        return ('%s %s(%s)' % (self.arg_man.c_proto_return_type(),
                                self.name, args))

    def all_dtypes(self):
        return self.arg_man.all_dtypes()


class SubroutineWrapper(ProcWrapper):
    pass


class FunctionWrapper(ProcWrapper):

    RETURN_ARG_NAME = constants.RETURN_ARG_NAME

    def __init__(self, wrapped):
        super(FunctionWrapper, self).__init__(wrapped)

    def _get_arg_man(self):
        self.arg_man = ArgWrapperManager(self.wrapped)

    def return_spec_declaration(self):
        return self.arg_man.return_spec_declaration()

    def proc_result_name(self):
        return self.arg_man.proc_result_name()


class ArgWrapperManager(object):

    def __init__(self, proc):
        self.proc = proc
        self.isfunction = (proc.kind == 'function')
        self.ret_arg = None
        if self.isfunction:
            ra = pyf.Argument(name=FunctionWrapper.RETURN_ARG_NAME,
                    dtype=proc.return_arg.dtype,
                    intent='out')
            self._orig_args = [ra] + list(proc.args)
        else:
            self._orig_args = list(proc.args)
        self.arg_wrappers = None
        self.errflag = pyf.Argument(name=constants.ERR_NAME,
                                dtype=pyf.default_integer,
                                intent='out')
        self.errstr = ErrStrArgWrapper()
        self._gen_wrappers()

    def _gen_wrappers(self):
        wargs = []
        for arg in self._orig_args + [self.errflag]:
            wargs.append(ArgWrapperFactory(arg))
        self.arg_wrappers = wargs + [self.errstr]
        if self.isfunction:
            self.ret_arg = self.arg_wrappers[0]

    def call_arg_list(self):
        cl = [argw.intern_name for argw in self.arg_wrappers
                if (argw.intern_name != FunctionWrapper.RETURN_ARG_NAME and
                    argw.intern_name != constants.ERR_NAME and
                    argw.intern_name != constants.ERRSTR_NAME and
                    argw.intern_name != _arg_name_mangler(FunctionWrapper.RETURN_ARG_NAME))]
        return cl

    def proc_result_name(self):
        return self.ret_arg.intern_name

    def extern_arg_list(self):
        ret = []
        for argw in self.arg_wrappers:
            ret.extend(argw.extern_arg_list())
        return ret

    def c_proto_args(self):
        ret = []
        for argw in self.arg_wrappers:
            ret.extend(argw.c_declarations())
        return ret

    def c_proto_return_type(self):
        return 'void'

    def param_declarations(self):
        proc_arg_man = self.proc.arg_man
        decls = []
        for o in proc_arg_man.order_declarations():
            if isinstance(o, pyf.Parameter):
                decls.append(o.declaration())
        return decls

    def arg_declarations(self):
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.extern_declarations())
        return decls

    def __return_spec_declaration(self):
        #XXX: demeter ???
        return self.return_arg_wrapper.extern_arg.declaration()

    def temp_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.intern_declarations())
        return decls

    def init_err(self):
        return "%s = FW_INIT_ERR__" % constants.ERR_NAME

    def no_err(self):
        return "%s = FW_NO_ERR__" % constants.ERR_NAME

    def pre_call_code(self):
        all_pcc = [self.init_err()]
        for argw in self.arg_wrappers:
            pcc = argw.pre_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def post_call_code(self):
        all_pcc = []
        wpprs = self.arg_wrappers[:]
        for argw in wpprs:
            pcc = argw.post_call_code()
            if pcc:
                all_pcc.extend(pcc)
        all_pcc += [self.no_err()]
        return all_pcc

    def _return_var_name(self):
        return self.return_arg_wrapper.intern_name

    def all_dtypes(self):
        return (self.proc.all_dtypes() +
                self.errstr.all_dtypes() +
                [self.errflag.dtype])


def ArgWrapperFactory(arg):
    if getattr(arg, 'dimension', None):
        if arg.dtype.type == 'character':
            return CharArrayArgWrapper(arg)

        # FIXME: uncomment when logical arrays use c_f_pointer
        # FIXME: currently this is a workaround for 4.3.3 <= gfortran version <
        # 4.4.

        # elif arg.dtype.type == 'logical':
            # return LogicalArrayArgWrapper(arg)

        return ArrayArgWrapper(arg)
    elif arg.dtype.type == 'logical':
        return LogicalWrapper(arg)
    elif arg.intent == 'hide':
        return HideArgWrapper(arg)
    elif arg.dtype.type == 'character':
        return CharArgWrapper(arg)
    else:
        return ArgWrapper(arg)


class ArgWrapperBase(object):

    is_array = False

    def pre_call_code(self):
        return []

    def post_call_code(self):
        return []

    def intern_declarations(self):
        return []

    def c_declarations(self):
        return []

    def call_arg_list(self):
        return []

    def extern_arg_list(self):
        return []


class ArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self.orig_arg = arg
        self.dtype = arg.dtype
        self.name = arg.name
        self.ktp = arg.ktp
        self.intent = arg.intent
        self._set_intern_name()
        self._set_intern_vars()
        self._set_extern_args()

    def _set_intern_name(self):
        self.intern_name = self.name

    def _set_intern_vars(self):
        self.intern_var = None

    def _set_extern_args(self):
        self.extern_arg = self.orig_arg
        self.extern_args = [self.extern_arg]

    def extern_arg_list(self):
        return [extern_arg.name for extern_arg in self.extern_args]

    def extern_declarations(self):
        return [extern_arg.declaration() for extern_arg in self.extern_args]

    def c_declarations(self):
        return [extern_arg.c_declaration() for extern_arg in self.extern_args]

    def intern_declarations(self):
        if self.intern_var:
            return [self.intern_var.declaration()]
        else:
            return []

class ErrStrArgWrapper(ArgWrapperBase):

    def __init__(self):
        self.arg = pyf.Argument(name=constants.ERRSTR_NAME,
                                dtype=pyf.default_character,
                                dimension=[constants.ERRSTR_LEN])
        self.dtype = self.arg.dtype
        self.name = self.arg.name
        self.intern_name = self.arg.name
        self.ktp = self.arg.ktp
        self.intent = None

    def c_declarations(self):
        return [self.arg.c_declaration()]

    def extern_arg_list(self):
        return [self.name]

    def extern_declarations(self):
        return [self.arg.declaration()]

    def intern_declarations(self):
        return []

    def all_dtypes(self):
        return [self.arg.dtype]


class HideArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_arg = None
        self._intern_var = \
                pyf.Var(name=arg.name, dtype=arg.dtype, dimension=None)
        self.value = arg.value
        assert self.value is not None
        self.intern_name = self._intern_var.name

    def extern_arg_list(self):
        return []

    def extern_declarations(self):
        return []

    def intern_declarations(self):
        return [self._intern_var.declaration()]

    def pre_call_code(self):
        return ["%s = (%s)" % (self._intern_var.name, self.value)]


class ArrayArgWrapper(ArgWrapper):

    is_array = True

    def _set_extern_args(self):
        self._arr_dims = []
        self.ndims = len(self.orig_arg.dimension)
        for idx in range(self.ndims):
            self._arr_dims.append(
                    pyf.Argument(name='%s_d%d' % (self.name, idx+1),
                                 dtype=pyf.dim_dtype, intent='in'))
        dim_names = [dim.name for dim in self._arr_dims]
        self.extern_arg = pyf.Argument(
                                name=self.name,
                                dtype=self.dtype,
                                intent=self.intent,
                                dimension=dim_names)
        self.extern_args = self._arr_dims + [self.extern_arg]

    def pre_call_code(self):
        dims = pyf.Dimension([dim.name for dim in self._arr_dims])
        ckstr = _dim_test(self.orig_arg.dimension, dims)
        if ckstr:
            return _err_test_block(
                            ckstr,
                            'FW_ARR_DIM__',
                            self.extern_arg.name)
        return []


class ScalarPtrWrapper(ArgWrapper):

    def _set_intern_name(self):
        self.intern_name = _arg_name_mangler(self.name)

    def _set_intern_vars(self):
        self.intern_var = pyf.Var(name=self.intern_name,
                                   dtype=self.orig_arg.dtype,
                                   isptr=True)

    def _set_extern_args(self):
        self.extern_arg = pyf.Argument(name=self.name,
                                        dtype=pyf.c_ptr_type,
                                        isvalue=True)
        self.extern_args = [self.extern_arg]

    def pre_call_code(self):
        return ['call c_f_pointer(%s, %s)' %
                (self.extern_arg.name,
                 self.intern_var.name)]


class LogicalWrapper(ScalarPtrWrapper):
    pass

class CharArgWrapper(ScalarPtrWrapper):

    def _set_intern_vars(self):
        self.len_arg = pyf.Argument(name="%s_len" % self.intern_name,
                                    dtype=pyf.dim_dtype,
                                    intent='in')
        self.is_assumed_len = (self.dtype.len == '*')
        self.orig_len = self.dtype.len
        if self.is_assumed_len:
            self.intern_dtype = pyf.CharacterType(self.ktp,
                                 len=self.len_arg.name,
                                 mangler="%s")
        else:
            self.intern_dtype = self.dtype
        self._set_intern_var()

    def _set_intern_var(self):
        self.intern_var = pyf.Var(name=self.intern_name,
                                       dtype=self.intern_dtype,
                                       isptr=True)

    def _set_extern_args(self):
        super(CharArgWrapper, self)._set_extern_args()
        self.extern_args = [self.len_arg] + self.extern_args

    def _err_ck_code(self):
        if self.is_assumed_len:
            ck_code = []
        else:
            test = ("%s .ne. %s" %
                    (self.orig_len, self.len_arg.name))
            errcode = "FW_CHAR_SIZE__"
            argname = self.extern_arg.name
            ck_code = _err_test_block(test, errcode, argname)

        return ck_code

    def pre_call_code(self):
        return self._err_ck_code() + \
                super(CharArgWrapper, self).pre_call_code()


class ArrayPtrArg(ArrayArgWrapper):

    def _set_intern_name(self):
        self.intern_name = _arg_name_mangler(self.name)

    def _set_intern_vars(self):
        self.intern_var = pyf.Var(name=self.intern_name,
                                   dtype=self.orig_arg.dtype,
                                   dimension=(':',)*len(self.orig_arg.dimension),
                                   isptr=True)

    def _set_extern_args(self):
        super(ArrayPtrArg, self)._set_extern_args()
        self.extern_arg = pyf.Argument(name=self.name,
                                       dtype=pyf.c_ptr_type,
                                       isvalue=True)
        self.extern_args = self._arr_dims + [self.extern_arg]

    def _pointer_call(self):
        dim_names = [dim.name for dim in self._arr_dims]
        return ['call c_f_pointer(%s, %s, (/ %s /))' %
                (self.extern_arg.name, self.intern_var.name, ', '.join(dim_names))]

    def _check_code(self):
        return super(ArrayPtrArg, self).pre_call_code()

    def pre_call_code(self):
        return self._check_code() + self._pointer_call()

# FIXME: uncomment when logical arrays use c_f_pointer
# FIXME: currently this is a workaround for 4.3.3 <= gfortran version < 4.4.
# class LogicalArrayArgWrapper(ArrayPtrArg):
    # pass


class CharArrayArgWrapper(ArrayPtrArg):

    def _set_intern_vars(self):
        self.len_arg = pyf.Argument(name="%s_len" % self.intern_name,
                                    dtype=pyf.dim_dtype,
                                    intent='in')
        self.is_assumed_len = (self.dtype.len == '*')
        self.orig_len = self.dtype.len
        if self.is_assumed_len:
            self.intern_dtype = pyf.CharacterType(self.ktp,
                                 len=self.len_arg.name,
                                 mangler="%s")
        else:
            self.intern_dtype = self.dtype

        self.intern_var = pyf.Var(name=self.intern_name,
                                       dtype=self.intern_dtype,
                                       dimension=(':',)*len(self.orig_arg.dimension),
                                       isptr=True)

    def _set_extern_args(self):
        super(CharArrayArgWrapper, self)._set_extern_args()
        self.extern_args = [self.len_arg] + self.extern_args


    def _check_code(self):
        orig_check = super(CharArrayArgWrapper, self)._check_code()
        if self.is_assumed_len:
            char_ck = []
        else:
            test = "%s .ne. %s" % (self.dtype.len, self.len_arg.name)
            char_ck = _err_test_block(test,
                                'FW_CHAR_SIZE__',
                                self.name)
        return char_ck + orig_check

    def _pointer_call(self):
        dim_names = [dim.name for dim in self._arr_dims]
        return [("call c_f_pointer(%s, %s, (/ %s /))" %
                    (self.name, self.intern_name, ', '.join(dim_names)))]
