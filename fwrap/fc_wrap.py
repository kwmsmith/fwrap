#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import pyf_iface as pyf
from fwrap import constants

def _arg_name_mangler(name):
    return "fw_%s" % name

def wrap_pyf_iface(ast):
    fc_wrapper = []
    for proc in ast:
        if proc.kind == 'function':
            fc_wrapper.append(FcFunction(wrapped=proc))
        elif proc.kind == 'subroutine':
            fc_wrapper.append(FcSubroutine(wrapped=proc))
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

def generate_fc_h(ast, ktp_header_name, buf, cfg):
    buf.putln('#include "%s"' % ktp_header_name)
    buf.putln('')
    buf.putln('#if !defined(FORTRAN_CALLSPEC)')
    buf.putln('#define FORTRAN_CALLSPEC')
    buf.putln('#endif')
    buf.putln('')
    if cfg.f77binding:
        import f77_config
        buf.write(f77_config.name_mangling_utility_code)
        buf.putln('')
    buf.putln('#if defined(__cplusplus)')
    buf.putln('extern "C" {')    
    buf.putln('#endif')
    for proc in ast:
        buf.putln(proc.c_prototype(cfg))
    buf.putln('#if defined(__cplusplus)')
    buf.putln('} /* extern "C" */')
    buf.putln('#endif')
    if cfg.f77binding:
        buf.putln('')
        buf.putln('#if !defined(NO_FORTRAN_MANGLING)')
        for proc in ast:
            buf.putln(proc.c_mangle_define())
        buf.putln('#endif')

def generate_interface(proc, buf, cfg, gmn=constants.KTP_MOD_NAME):
    if cfg.f77binding:
        buf.putln('external %s' % proc.name)
    else:
        buf.putln('interface')
        buf.indent()
        buf.putln(proc.proc_declaration(cfg))
        buf.indent()
        proc.proc_preamble(gmn, buf, cfg)
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


class FcProcedure(object):

    def __init__(self, wrapped):
        self.name = constants.PROC_SUFFIX_TMPL % wrapped.name
        self.wrapped = wrapped
        self.arg_man = None
        self._get_arg_man()

    def _get_arg_man(self):
        self.arg_man = FcArgManager(self.wrapped)

    def wrapped_name(self):
        return self.wrapped.name

    def proc_end(self):
        return "end subroutine %s" % self.name

    def proc_preamble(self, ktp_mod, buf, cfg):
        if not cfg.f77binding:
            buf.putln('use %s' % ktp_mod)
        buf.putln('implicit none')
        if cfg.f77binding:
            for line in constants.get_fortran_constants_utility_code(f77=True):
                buf.putln(line)
            buf.putln("character C_NULL_CHAR")
            buf.putln("parameter (C_NULL_CHAR = '\\0')")
        for declaration in (self.arg_declarations(cfg) +
                            self.param_declarations(cfg)):
            buf.putln(declaration)

    def generate_wrapper(self, buf, cfg, gmn=constants.KTP_MOD_NAME):
        buf.putln(self.proc_declaration(cfg))
        buf.indent()
        self.proc_preamble(gmn, buf, cfg)
        generate_interface(self.wrapped, buf, cfg, gmn)
        self.temp_declarations(buf, cfg)
        self.pre_call_code(buf, cfg)
        self.proc_call(buf, cfg)
        self.post_call_code(buf, cfg)
        buf.dedent()
        buf.putln(self.proc_end())

    def proc_declaration(self, cfg):
        if not cfg.f77binding:
            return 'subroutine %s(%s) bind(c, name="%s")' % \
                   (self.name, ', '.join(self.extern_arg_list()),
                    self.name)
        else:
            return 'subroutine %s(%s) ' % \
                   (self.name, ', '.join(self.extern_arg_list()))

    def temp_declarations(self, buf, cfg):
        for declaration in self.arg_man.temp_declarations(cfg):
            buf.putln(declaration)

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self, cfg):
        return self.arg_man.arg_declarations(cfg)

    def param_declarations(self, cfg):
        return self.arg_man.param_declarations(cfg)

    def pre_call_code(self, buf, cfg):
        for line in self.arg_man.pre_call_code(cfg):
            buf.putln(line)

    def post_call_code(self, buf, cfg):
        for line in self.arg_man.post_call_code(cfg):
            buf.putln(line)

    def proc_call(self, buf, cfg):
        proc_call = "%s(%s)" % (self.wrapped.name,
                                ', '.join(self.call_arg_list(cfg)))
        if isinstance(self, FcSubroutine):
            buf.putln("call %s" % proc_call)
        elif isinstance(self, FcFunction):
            buf.putln("%s = %s" % (self.proc_result_name(), proc_call))

    def call_arg_list(self, cfg):
        return self.arg_man.call_arg_list(cfg)

    def c_prototype(self, cfg):
        if not cfg.f77binding:
            return "FORTRAN_CALLSPEC %s;" % self.cy_prototype()
        else:
            return "FORTRAN_CALLSPEC %s F_FUNC(%s,%s)(%s);" % (
                self.arg_man.c_proto_return_type(),
                self.name.lower(),
                self.name.upper(),
                ", ".join(self.arg_man.c_proto_args()))

    def c_mangle_define(self):
        return '#define %s F_FUNC(%s,%s)' % (self.name,
                                             self.name.lower(),
                                             self.name.upper())

    def cy_prototype(self):
        args = ", ".join(self.arg_man.c_proto_args())
        return ('%s %s(%s)' % (self.arg_man.c_proto_return_type(),
                                self.name, args))

    def all_dtypes(self):
        return self.arg_man.all_dtypes()


class FcSubroutine(FcProcedure):
    pass


class FcFunction(FcProcedure):

    RETURN_ARG_NAME = constants.RETURN_ARG_NAME

    def __init__(self, wrapped):
        super(FcFunction, self).__init__(wrapped)

    def _get_arg_man(self):
        self.arg_man = FcArgManager(self.wrapped)

    def return_spec_declaration(self):
        return self.arg_man.return_spec_declaration()

    def proc_result_name(self):
        return self.arg_man.proc_result_name()


class FcArgManager(object):

    def __init__(self, proc):
        self.proc = proc
        self.isfunction = (proc.kind == 'function')
        self.ret_arg = None
        if self.isfunction:
            ra = pyf.Argument(name=FcFunction.RETURN_ARG_NAME,
                    dtype=proc.return_arg.dtype,
                    intent='out')
            self._orig_args = [ra] + list(proc.args)
        else:
            self._orig_args = list(proc.args)
        self.arg_wrappers = None
        self.errflag = pyf.Argument(name=constants.ERR_NAME,
                                dtype=pyf.default_integer,
                                intent='out')
        self.errstr = FcErrStrArg()
        self._gen_wrappers()

    def _gen_wrappers(self):
        wargs = []
        for arg in self._orig_args + [self.errflag]:
            wargs.append(FcArgFactory(arg))
        self.arg_wrappers = wargs + [self.errstr]
        if self.isfunction:
            self.ret_arg = self.arg_wrappers[0]

    def call_arg_list(self, cfg):
        intern_names = [argw.get_call_name(cfg) for argw in self.arg_wrappers]
        cl = [intern_name for intern_name in intern_names
                if (intern_name != FcFunction.RETURN_ARG_NAME and
                    intern_name != constants.ERR_NAME and
                    intern_name != constants.ERRSTR_NAME and
                    intern_name != _arg_name_mangler(FcFunction.RETURN_ARG_NAME))]
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
            ret.extend(argw.c_types())
        return ret

    def c_proto_return_type(self):
        return 'void'

    def param_declarations(self, cfg):
        proc_arg_man = self.proc.arg_man
        decls = []
        for o in proc_arg_man.order_declarations():
            if isinstance(o, pyf.Parameter):
                decls.append(o.declaration(cfg))
        return decls

    def arg_declarations(self, cfg):
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.extern_declarations(cfg))
        return decls

    def __return_spec_declaration(self):
        #XXX: demeter ???
        return self.return_arg_wrapper.extern_arg.declaration()

    def temp_declarations(self, cfg):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.intern_declarations(cfg))
        return decls

    def assign_err_flag(self, value, cfg):
        if cfg.f77binding:
            value = str(constants.ERR_CODES[value])
        return "%s = %s" % (constants.ERR_NAME, value)

    def no_err(self):
        if cfg.f77binding:
            return "%s = %d" % (
                constants.ERR_NAME,
                constants.ERR_CODES['FW_NO_ERR__'])
        else:
            return "%s = FW_NO_ERR__" % constants.ERR_NAME

    def pre_call_code(self, cfg):
        all_pcc = [self.assign_err_flag('FW_INIT_ERR__', cfg)]
        for argw in self.arg_wrappers:
            pcc = argw.pre_call_code(cfg)
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def post_call_code(self, cfg):
        all_pcc = []
        wpprs = self.arg_wrappers[:]
        for argw in wpprs:
            pcc = argw.post_call_code()
            if pcc:
                all_pcc.extend(pcc)
        all_pcc += [self.assign_err_flag('FW_NO_ERR__', cfg)]
        return all_pcc

    def _return_var_name(self):
        return self.return_arg_wrapper.intern_name

    def all_dtypes(self):
        return (self.proc.all_dtypes() +
                self.errstr.all_dtypes() +
                [self.errflag.dtype])


def FcArgFactory(arg):
    if getattr(arg, 'dimension', None):
        if arg.dtype.type == 'character':
            return FcCharArrayArg(arg)

        # FIXME: uncomment when logical arrays use c_f_pointer
        # FIXME: currently this is a workaround for 4.3.3 <= gfortran version <
        # 4.4.

        # elif arg.dtype.type == 'logical':
            # return FcLogicalArrayArg(arg)

        return FcArrayArg(arg)
    elif arg.dtype.type == 'logical':
        return FcLogicalArg(arg)
    elif arg.dtype.type == 'character':
        return FcCharArg(arg)
    else:
        return FcArg(arg)


class FcArgBase(object):

    is_array = False

    def pre_call_code(self, cfg):
        return []

    def post_call_code(self):
        return []

    def intern_declarations(self):
        return []

    def c_declarations(self):
        return []

    def call_arg_list(self, cfg):
        return []

    def extern_arg_list(self):
        return []

    def get_call_name(self, cfg):
        return self.intern_name

class FcArg(FcArgBase):

    def __init__(self, arg):
        self.orig_arg = arg
        self.dtype = arg.dtype
        self.name = arg.name
        self.ktp = arg.ktp
        self.intent = arg.intent
        self.init_code = arg.init_code
        self.hide_in_wrapper = arg.hide_in_wrapper
        self.check = arg.check
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

    def extern_declarations(self, cfg):
        return [extern_arg.declaration(cfg)
                for extern_arg in self.extern_args]

    def c_declarations(self):
        return [extern_arg.c_declaration()
                for extern_arg in self.extern_args]

    def c_types(self):
        return [extern_arg.c_type() for extern_arg in self.extern_args]

    def intern_declarations(self, cfg):
        if self.intern_var:
            return [self.intern_var.declaration(cfg)]
        else:
            return []

    def equal_up_to_type(self, other):
        if type(self) is not type(other):
            return False
        if not (self.intent == other.intent and
                self.init_code == other.init_code and
                self.hide_in_wrapper == other.hide_in_wrapper and
                self.check == other.check):
            return False
        sd = self.orig_arg.dimension
        od = other.orig_arg.dimension
        if sd is not None:
            if od is None:
                return False
            if len(sd.dims) != len(od.dims):
                return False
            if sd.dims != od.dims: # pyf_iface.Dim implements __eq__
                return False
        return True
                

class FcErrStrArg(FcArgBase):

    def __init__(self):
        self.arg = pyf.Argument(name=constants.ERRSTR_NAME,
                                dtype=pyf.default_character,
                                dimension=[constants.ERRSTR_LEN])
        self.dtype = self.arg.dtype
        self.name = self.arg.name
        self.intern_name = self.arg.name
        self.ktp = self.arg.ktp
        self.intent = None

    def c_types(self):
        return [self.arg.c_type()]

    def c_declarations(self):
        return [self.arg.c_declaration()]

    def extern_arg_list(self):
        return [self.name]

    def extern_declarations(self, cfg):
        x = self.arg.declaration(cfg)
        if cfg.f77binding:
            x = x.replace(constants.ERRSTR_LEN,
                          str(constants.FORT_MAX_ARG_NAME_LEN))
        return [x]

    def intern_declarations(self, cfg):
        return []

    def all_dtypes(self):
        return [self.arg.dtype]

    def equal_up_to_type(self, other):
        return type(self) is type(other)


class FcArrayArg(FcArg):

    is_array = True
    shape_pattern = '%s_shape__'

    def _set_extern_args(self):
        self._arr_dims = []
        self.ndims = len(self.orig_arg.dimension)

        self.shape_arg = pyf.Argument(name=self.shape_pattern % self.name,
                                      dtype=pyf.dim_dtype,
                                      intent='in',
                                      dimension=[str(self.ndims)])
        
        self._dimension_exprs = ['%s(%d)' % (self.shape_arg.name, i)
                                 for i in range(1, self.ndims + 1)]
        self.extern_arg = pyf.Argument(
                                name=self.name,
                                dtype=self.dtype,
                                intent=self.intent,
                                dimension=self._dimension_exprs)
        self.extern_args = [self.shape_arg, self.extern_arg]

    def pre_call_code(self, cfg):
        dims = pyf.Dimension(self._dimension_exprs)
        ckstr = _dim_test(self.orig_arg.dimension, dims)
        if ckstr:
            return _err_test_block(
                            ckstr,
                            'FW_ARR_DIM__',
                            self.extern_arg.name)
        return []

class FcScalarPtrArg(FcArg):

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

    # Following methods:
    # In the case of iso_c_binding, we take the argument as a c_ptr
    # and then cast to the internal type using c_f_pointer.
    # For f77binding, we declare the variable directly (with the
    # "internal" type, using the external name).

    def get_call_name(self, cfg):
        if cfg.f77binding:
            return self.name
        else:
            return self.intern_name

    def pre_call_code(self, cfg):
        if cfg.f77binding:
            return []
        else:
            return ['call c_f_pointer(%s, %s)' %
                    (self.extern_arg.name,
                     self.intern_var.name)]

    def extern_declarations(self, cfg):
        if cfg.f77binding:
            f77_extern_var = pyf.Var(name=self.name,
                                     dtype=self.intern_dtype,
                                     isptr=False)
            return [self.len_arg.declaration(cfg),
                    f77_extern_var.declaration(cfg)]
        else:
            return super(FcScalarPtrArg, self).extern_declarations(cfg)

    def intern_declarations(self, cfg):
        if cfg.f77binding:
            return []
        else:
            return super(FcScalarPtrArg, self).intern_declarations(cfg)


class FcLogicalArg(FcScalarPtrArg):
    pass

class FcCharArg(FcScalarPtrArg):

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
        super(FcCharArg, self)._set_extern_args()
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

    def pre_call_code(self, cfg):
        return self._err_ck_code() + \
                super(FcCharArg, self).pre_call_code(cfg)


class FcArrayPtrArg(FcArrayArg):

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

    def _check_code(self, cfg):
        return super(ArrayPtrArg, self).pre_call_code(cfg)

    def pre_call_code(self, cfg):
        return self._check_code(cfg) + self._pointer_call()

# FIXME: uncomment when logical arrays use c_f_pointer
# FIXME: currently this is a workaround for 4.3.3 <= gfortran version < 4.4.
# class FcLogicalArrayArg(FcArrayPtrArg):
    # pass


class FcCharArrayArg(FcArrayPtrArg):

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
        super(FcCharArrayArg, self)._set_extern_args()
        self.extern_args = [self.len_arg] + self.extern_args


    def _check_code(self, cfg):
        orig_check = super(FcCharArrayArg, self)._check_code(cfg)
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
