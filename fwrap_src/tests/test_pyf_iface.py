from fwrap_src import pyf_iface as pyf
from nose.tools import ok_, eq_, set_trace

class test_program_units(object):
    def test_function(self):
        ffun = pyf.Function(name="fort_function",
                args=(),
                return_type=pyf.default_integer)
        ok_(ffun.name == 'fort_function')
        ok_(ffun.return_arg.dtype is pyf.default_integer)

    def test_function_args(self):
        pyf.Function(name="ffun",
                args=('a', 'b', 'c'),
                return_type=pyf.default_integer)

    def test_subroutine(self):
        pyf.Subroutine(name='subr',
                args=())

    def test_module(self):
        pyf.Module(name='mod')

    def test_module_use(self):
        mod1 = pyf.Module(
                name='mod1',
                mod_objects=[
                    pyf.Var(name='i', dtype=pyf.default_integer),
                    pyf.Var(name='r', dtype=pyf.default_real),
                    pyf.Var(name='c', dtype=pyf.default_complex),
                    ]
                )

        pyf.Module(
                name='mod',
                uses=[
                    pyf.Use(mod1, only=('i', 'r')),
                    ]
                )

class test_array_arg_wrapper(object):

    def setup(self):
        self.real_arr_arg = pyf.Argument(name='real_arr_arg', dtype=pyf.default_real, dimension=(':',':',':'), intent='out')
        self.int_arr_arg = pyf.Argument(name='arr_arg', dtype=pyf.default_integer, dimension=(':',':'), intent='inout')
        self.int_arr_wrapper = pyf.ArrayArgWrapper(self.int_arr_arg)
        self.real_arr_wrapper = pyf.ArrayArgWrapper(self.real_arr_arg)

        self.real_explicit_arg = pyf.Argument(name='real_exp_arg', dtype=pyf.default_real, dimension=('d1', 'd2', 'd3'), intent='inout')

    def test_extern_decls(self):
        int_decls = '''\
integer(fwrap_default_int), intent(in) :: arr_arg_d1
integer(fwrap_default_int), intent(in) :: arr_arg_d2
integer(fwrap_default_int), dimension(arr_arg_d1, arr_arg_d2), intent(inout) :: arr_arg
'''
        real_decls = '''\
integer(fwrap_default_int), intent(in) :: real_arr_arg_d1
integer(fwrap_default_int), intent(in) :: real_arr_arg_d2
integer(fwrap_default_int), intent(in) :: real_arr_arg_d3
real(fwrap_default_real), dimension(real_arr_arg_d1, real_arr_arg_d2, real_arr_arg_d3), intent(out) :: real_arr_arg
'''
        eq_(self.int_arr_wrapper.extern_declarations(), int_decls.splitlines())
        eq_(self.real_arr_wrapper.extern_declarations(), real_decls.splitlines())

    def test_extern_arg_list(self):
        eq_(self.int_arr_wrapper.extern_arg_list(), ['arr_arg_d1', 'arr_arg_d2', 'arr_arg'])
        eq_(self.real_arr_wrapper.extern_arg_list(), ['real_arr_arg_d1', 'real_arr_arg_d2', 'real_arr_arg_d3', 'real_arr_arg'])

class test_arg_wrapper(object):

    def setup(self):
        dint = pyf.IntegerType('fwrap_int')
        dlgcl = pyf.default_logical

        self.int_arg = pyf.Argument(name='int', dtype=dint, intent='inout')
        self.int_arg_wrap = pyf.ArgWrapperFactory(self.int_arg)

        self.lgcl_arg = pyf.Argument(name='lgcl', dtype=dlgcl, intent='inout')
        self.lgcl_arg_wrap = pyf.ArgWrapperFactory(self.lgcl_arg)

        self.lgcl_arg_in = pyf.Argument(name='lgcl_in', dtype=dlgcl, intent='in')
        self.lgcl_arg_in_wrap = pyf.ArgWrapperFactory(self.lgcl_arg_in)

    def test_extern_int_arg(self):
        eq_(self.int_arg_wrap.extern_declarations(), [self.int_arg.declaration()])

    def test_intern_int_var(self):
        eq_(self.int_arg_wrap.intern_declarations(), [])

    def test_pre_call_code_int(self):
        eq_(self.int_arg_wrap.pre_call_code(), [])

    def test_post_call_code_int(self):
        eq_(self.int_arg_wrap.post_call_code(), [])

    def test_extern_lgcl_arg(self):
        eq_(self.lgcl_arg_wrap.extern_declarations(),
                ['logical(fwrap_default_logical), intent(inout) :: lgcl'])
        eq_(self.lgcl_arg_in_wrap.extern_declarations(),
                ['logical(fwrap_default_logical), intent(in) :: lgcl_in'])

    def test_intern_lgcl_var(self):
        eq_(self.lgcl_arg_wrap.intern_declarations(), [])
        eq_(self.lgcl_arg_in_wrap.intern_declarations(), [])

    def _test_pre_call_code(self):
        for argw in (self.lgcl_arg_wrap, self.lgcl_arg_in_wrap):
            pcc = '''\
if(%(extern_arg)s .ne. 0) then
    %(intern_var)s = .true.
else
    %(intern_var)s = .false.
end if
''' % {'extern_arg' : argw._extern_arg.name,
       'intern_var' : argw._intern_var.name}
            eq_(argw.pre_call_code(), pcc.splitlines())

    def _test_post_call_code_convert(self):
        for argw in (self.lgcl_arg_wrap, self.lgcl_arg_in_wrap):
            pcc = '''\
if(%(intern_var)s) then
    %(extern_arg)s = 1
else
    %(extern_arg)s = 0
end if
''' % {'extern_arg' : argw._extern_arg.name,
       'intern_var' : argw._intern_var.name}
            eq_(argw.post_call_code(), pcc.splitlines())

    def test_post_call_code(self):
        for argw in (self.lgcl_arg_wrap, self.lgcl_arg_in_wrap):
            eq_(argw.post_call_code(), [])

class test_arg_manager_return(object):

    def setup(self):
        dlgcl = pyf.default_logical
        dint = pyf.IntegerType(ktp='fwrap_int')
        self.lgcl = pyf.Argument(name='ll', dtype=dlgcl, intent='out', is_return_arg=True)
        self.int = pyf.Argument(name='int', dtype=dint, intent='out', is_return_arg=True)
        self.am_lgcl = pyf.ArgWrapperManager([], self.lgcl)
        self.am_int = pyf.ArgWrapperManager([], self.int)

    def test_declarations(self):
        decl = '''\
logical(fwrap_default_logical) :: ll
'''.splitlines()
        eq_(self.am_lgcl.arg_declarations(), decl)

    def test_temp_declarations(self):
        eq_(self.am_lgcl.temp_declarations(), [])

class test_arg_manager(object):
    
    def test_declaration_order(self):
        array_arg = pyf.Argument('arr', pyf.default_integer, 'in', dimension=('d1', 'd2'))
        d1 = pyf.Argument('d1', pyf.default_integer, 'in')
        d2 = pyf.Argument('d2', pyf.default_integer, 'in')
        am = pyf.ArgManager([array_arg, d2, d1])
        decls = '''\
integer(fwrap_default_int), intent(in) :: d2
integer(fwrap_default_int), intent(in) :: d1
integer(fwrap_default_int), dimension(d1, d2), intent(in) :: arr
'''
        eq_(am.arg_declarations(), decls.splitlines())

class test_arg_wrapper_manager(object):
    
    def setup(self):
        dlgcl = pyf.default_logical
        dint = pyf.IntegerType(ktp='fwrap_int')
        self.lgcl1 = pyf.Argument(name='lgcl1', dtype=dlgcl, intent='inout')
        self.lgcl2 = pyf.Argument(name='lgcl2', dtype=dlgcl, intent='inout')
        self.intarg = pyf.Argument(name='int', dtype=dint, intent='inout')
        self.args = [self.lgcl1, self.lgcl2, self.intarg]
        self.l1wrap = pyf.ArgWrapper(self.lgcl1)
        self.l2wrap = pyf.ArgWrapper(self.lgcl2)
        self.am = pyf.ArgWrapperManager(self.args)

    def test_arg_declarations(self):
        decls = '''\
logical(fwrap_default_logical), intent(inout) :: lgcl1
logical(fwrap_default_logical), intent(inout) :: lgcl2
integer(fwrap_int), intent(inout) :: int
'''.splitlines()
        eq_(self.am.arg_declarations(), decls)

    def _test_arg_declarations_convert(self):
        decls = '''\
integer(fwrap_default_int), intent(inout) :: lgcl1
integer(fwrap_default_int), intent(inout) :: lgcl2
integer(fwrap_int), intent(inout) :: int
'''.splitlines()
        eq_(self.am.arg_declarations(), decls)

    def _test_temp_declarations(self):
        decls = '''\
logical(fwrap_default_logical) :: lgcl1_tmp
logical(fwrap_default_logical) :: lgcl2_tmp
'''.splitlines()
        eq_(self.am.temp_declarations(), decls)

    def test_pre_call_code(self):
        pcc = self.l1wrap.pre_call_code() + self.l2wrap.pre_call_code()
        eq_(self.am.pre_call_code(), pcc)

    def test_post_call_code(self):
        pcc = self.l1wrap.post_call_code() + self.l2wrap.post_call_code()
        eq_(self.am.post_call_code(), pcc)

    def test_extern_arg_list(self):
        al = 'lgcl1 lgcl2 int'.split()
        eq_(self.am.extern_arg_list(), al)

    def test_call_arg_list(self):
        cl = 'lgcl1 lgcl2 int'.split()
        eq_(self.am.call_arg_list(), cl)

    #TODO
    def _test_arg_mangle_collision(self):
        # when two passed logical arguments have the name 'lgcl' and 'lgcl_tmp'
        # the intern_var for lgcl can't be named 'lgcl_tmp'
        # this needs to be detected and resolved.
        pass
