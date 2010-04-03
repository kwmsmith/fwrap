from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from fwrap_src.code import CodeBuffer

from tutils import compare

from nose.tools import ok_, eq_, set_trace

class test_empty_func(object):

    def setup(self):
        self.empty_func = pyf.Function(name='empty_func',
                        args=(),
                        return_type=pyf.default_integer)
        self.buf = CodeBuffer()

    def teardown(self):
        del self.empty_func
        del self.buf

    def test_generate_header_empty_func(self):
        pname = "DP"
        fc_wrap.GenCHeader(pname).generate([self.empty_func], self.buf)
        header_file = '''
#include "config.h"
fwrap_default_integer empty_func_c();
'''.splitlines()
        eq_(header_file, self.buf.getvalue().splitlines())

    def test_generate_pxd_empty_func(self):
        pname = "DP"
        fc_wrap.GenPxd(pname).generate([self.empty_func], self.buf)
        pxd_file = '''
cdef extern from "config.h":
    ctypedef int fwrap_default_integer

cdef extern:
    fwrap_default_integer empty_func_c()
'''.splitlines()
        eq_(pxd_file, self.buf.getvalue().splitlines())

def test_gen_fortran_one_arg_func():
    one_arg = pyf.Subroutine(
            name='one_arg',
            args=[pyf.Argument(name='a',
                               dtype=pyf.default_integer,
                               intent="in")])
    one_arg_wrapped = fc_wrap.SubroutineWrapper(name='one_arg_c', wrapped=one_arg)
    buf = CodeBuffer()
    one_arg_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    fort_file = '''\
    subroutine one_arg_c(a) bind(c, name="one_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(fwrap_default_integer), intent(in) :: a
        interface
            subroutine one_arg(a)
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer), intent(in) :: a
            end subroutine one_arg
        end interface
        call one_arg(a)
    end subroutine one_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_gen_empty_func_wrapper():
    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_type=pyf.default_integer)
    empty_func_wrapper = fc_wrap.FunctionWrapper(name='empty_func_c', wrapped=empty_func)
                      
    empty_func_wrapped = '''\
    function empty_func_c() bind(c, name="empty_func_c")
        use fwrap_ktp_mod
        implicit none
        integer(fwrap_default_integer) :: empty_func_c
        interface
            function empty_func()
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer) :: empty_func
            end function empty_func
        end interface
        empty_func_c = empty_func()
    end function empty_func_c
'''
    buf = CodeBuffer()
    empty_func_wrapper.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    compare(empty_func_wrapped, buf.getvalue())

def test_gen_iface():

    def gen_iface_gen(ast, istr):
        buf = CodeBuffer()
        #ast.generate_interface(buf)
        fc_wrap.generate_interface(ast, fc_wrap.KTP_MOD_NAME, buf)
        compare(istr, buf.getvalue())


    many_arg_subr = pyf.Subroutine(name='many_arg_subr',
                         args=[pyf.Argument(name='arg1',
                                            dtype=pyf.ComplexType('sik_10_20'),
                                            intent='in'),
                               pyf.Argument(name='arg2',
                                            dtype=pyf.RealType('double_precision'),
                                            intent='inout'),
                               pyf.Argument(name='arg3',
                                            dtype=pyf.IntegerType('int_x_8'),
                                            intent='out')])
    many_arg_subr_iface = '''\
    interface
        subroutine many_arg_subr(arg1, arg2, arg3)
            use fwrap_ktp_mod
            implicit none
            complex(fwrap_sik_10_20), intent(in) :: arg1
            real(fwrap_double_precision), intent(inout) :: arg2
            integer(fwrap_int_x_8), intent(out) :: arg3
        end subroutine many_arg_subr
    end interface
'''

    one_arg_func = pyf.Function(name='one_arg_func',
                        args=[pyf.Argument(name='arg1',
                                           dtype=pyf.default_real,
                                           intent='inout')],
                        return_type=pyf.default_integer)
    one_arg_func_iface = '''\
    interface
        function one_arg_func(arg1)
            use fwrap_ktp_mod
            implicit none
            real(fwrap_default_real), intent(inout) :: arg1
            integer(fwrap_default_integer) :: one_arg_func
        end function one_arg_func
    end interface
'''

    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_type=pyf.default_integer)
    empty_func_iface = '''\
    interface
        function empty_func()
            use fwrap_ktp_mod
            implicit none
            integer(fwrap_default_integer) :: empty_func
        end function empty_func
    end interface
'''
    data = [(many_arg_subr, many_arg_subr_iface),
            (one_arg_func, one_arg_func_iface),
            (empty_func, empty_func_iface)]

    for ast, iface in data:
        yield gen_iface_gen, ast, iface

def test_intent_hide():
    hide_arg_subr = pyf.Subroutine('hide_subr',
                            args=[pyf.Argument('hide_arg',
                                        dtype=pyf.default_integer,
                                        intent='hide',
                                        value='10')])
    wppr = fc_wrap.SubroutineWrapper(name='hide_subr_c', wrapped=hide_arg_subr)
    buf = CodeBuffer()
    wppr.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    check = '''\
    subroutine hide_subr_c() bind(c, name="hide_subr_c")
        use fwrap_ktp_mod
        implicit none
        interface
            subroutine hide_subr(hide_arg)
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer) :: hide_arg
            end subroutine hide_subr
        end interface
        integer(fwrap_default_integer) :: hide_arg
        hide_arg = (10)
        call hide_subr(hide_arg)
    end subroutine hide_subr_c
'''
    compare(check, buf.getvalue())
def _test_check():
    # this gets complicated...
    check_subr = pyf.Subroutine('check_subr',
                        args=[pyf.Argument('arr',
                                        dtype=pyf.default_integer,
                                        intent='in',
                                        dimension=('d1','d2')),
                              pyf.Argument('d1',
                                        dtype=pyf.default_integer,
                                        intent='in'),
                              pyf.Argument('d2',
                                        dtype=pyf.default_integer,
                                        intent='in')],
                        check=['d1 == size(arr, 1)',
                               'd2 == size(arr, 2)'])

    wppr = fc_wrap.SubroutineWrapper(name='check_subr_c', wrapped=check_subr)
    buf = CodeBuffer()
    wppr.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    check = '''\
    subroutine check_subr_c(arr_d1, arr_d2, arr, d1, d2, fw_error)
        use fwrap_ktp_mod
        implicit none
        integer, intent(in) :: arr_d1
        integer, intent(in) :: arr_d2
        integer, dimension(arr_d1, arr_d2), intent(in) :: arr
        integer, intent(in) :: d1
        integer, intent(in) :: d2
        integer, intent(out) :: fw_error
        interface
            subroutine check_subr(arr, d1, d2)
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer), intent(in) :: d1
                integer(fwrap_default_integer), intent(in) :: d2
                integer(fwrap_default_integer), dimension(d1, d2), intent(in) :: arr
            end subroutine check_subr
        end interface
        fw_error = 0
        if(.not. (d1 == size(arr, 1))) then
            fw_error = 1
            return
        endif
        if(.not. (d2 == size(arr, 2))) then
            fw_error = 2
            return
        endif
        call check_subr(arr, d1, d2)
    end subroutine check_subr_c
'''
    compare(check, buf.getvalue())

def test_logical_function():
    lgcl_fun = pyf.Function(name='lgcl_fun', args=[],
                            return_type=pyf.LogicalType(ktp='lgcl'))
    lgcl_fun_wrapped = fc_wrap.FunctionWrapper(name='lgcl_fun_c', wrapped=lgcl_fun)
    buf = CodeBuffer()
    lgcl_fun_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    fort_file = '''\
    function lgcl_fun_c() bind(c, name="lgcl_fun_c")
        use fwrap_ktp_mod
        implicit none
        logical(fwrap_lgcl) :: lgcl_fun_c
        interface
            function lgcl_fun()
                use fwrap_ktp_mod
                implicit none
                logical(fwrap_lgcl) :: lgcl_fun
            end function lgcl_fun
        end interface
        lgcl_fun_c = lgcl_fun()
    end function lgcl_fun_c
'''
    compare(fort_file, buf.getvalue())

def test_logical_wrapper():
    lgcl_arg = pyf.Subroutine(name='lgcl_arg',
                           args=[pyf.Argument(name='lgcl',
                                              dtype=pyf.LogicalType(ktp='lgcl_ktp'),
                                              intent="inout")])
    lgcl_arg_wrapped = fc_wrap.SubroutineWrapper(name='lgcl_arg_c', wrapped=lgcl_arg)
    buf = CodeBuffer()
    lgcl_arg_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    fort_file = '''\
    subroutine lgcl_arg_c(lgcl) bind(c, name="lgcl_arg_c")
        use fwrap_ktp_mod
        implicit none
        logical(fwrap_lgcl_ktp), intent(inout) :: lgcl
        interface
            subroutine lgcl_arg(lgcl)
                use fwrap_ktp_mod
                implicit none
                logical(fwrap_lgcl_ktp), intent(inout) :: lgcl
            end subroutine lgcl_arg
        end interface
        call lgcl_arg(lgcl)
    end subroutine lgcl_arg_c
'''
    compare(fort_file, buf.getvalue())


def test_assumed_shape_int_array():
    arr_arg = pyf.Subroutine(name='arr_arg',
                           args=[pyf.Argument(name='arr',
                                              dtype=pyf.default_integer,
                                              dimension=(':',':'),
                                              intent="inout")])
    arr_arg_wrapped = fc_wrap.SubroutineWrapper(name='arr_arg_c', wrapped=arr_arg)
    buf = CodeBuffer()
    arr_arg_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    fort_file = '''\
    subroutine arr_arg_c(arr_d1, arr_d2, arr) bind(c, name="arr_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(fwrap_default_integer), intent(in) :: arr_d1
        integer(fwrap_default_integer), intent(in) :: arr_d2
        integer(fwrap_default_integer), dimension(arr_d1, arr_d2), intent(inout) :: arr
        interface
            subroutine arr_arg(arr)
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer), dimension(:, :), intent(inout) :: arr
            end subroutine arr_arg
        end interface
        call arr_arg(arr)
    end subroutine arr_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_explicit_shape_int_array():
    arr_arg = pyf.Subroutine(name='arr_arg',
                           args=[pyf.Argument(name='arr',
                                              dtype=pyf.default_integer,
                                              dimension=('d1', 'd2'),
                                              intent="inout"),
                                pyf.Argument(name='d1', dtype=pyf.default_integer,
                                                intent='in'),
                                pyf.Argument(name='d2', dtype=pyf.default_integer,
                                                intent='in')
                                ])
    arr_arg_wrapped = fc_wrap.SubroutineWrapper(name='arr_arg_c', wrapped=arr_arg)
    buf = CodeBuffer()
    arr_arg_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    fort_file = '''\
    subroutine arr_arg_c(arr_d1, arr_d2, arr, d1, d2) bind(c, name="arr_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(fwrap_default_integer), intent(in) :: arr_d1
        integer(fwrap_default_integer), intent(in) :: arr_d2
        integer(fwrap_default_integer), dimension(arr_d1, arr_d2), intent(inout) :: arr
        integer(fwrap_default_integer), intent(in) :: d1
        integer(fwrap_default_integer), intent(in) :: d2
        interface
            subroutine arr_arg(arr, d1, d2)
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer), intent(in) :: d1
                integer(fwrap_default_integer), intent(in) :: d2
                integer(fwrap_default_integer), dimension(d1, d2), intent(inout) :: arr
            end subroutine arr_arg
        end interface
        call arr_arg(arr, d1, d2)
    end subroutine arr_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_many_arrays():
    arr_args = pyf.Subroutine(name='arr_args',
                           args=[
                                    pyf.Argument('assumed_size', pyf.default_integer, "inout", dimension=('d1','*')),
                                    pyf.Argument('d1', pyf.default_integer, 'in'),
                                    pyf.Argument('assumed_shape', pyf.default_logical, 'out', dimension=(':', ':')),
                                    pyf.Argument('explicit_shape', pyf.default_complex, 'inout', ('c1', 'c2')),
                                    pyf.Argument('c1', pyf.default_integer, 'inout'),
                                    pyf.Argument('c2', pyf.default_integer)
                                ])
    arr_args_wrapped = fc_wrap.SubroutineWrapper(name='arr_args_c', wrapped=arr_args)
    buf = CodeBuffer()
    arr_args_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    compare(many_arrays_text, buf.getvalue())

def _test_parameters():
    param_func = pyf.Function(name='param_func',
                              params=[pyf.Parameter(name='FOO', dtype=pyf.default_integer, value='kind(1.0D0)'),
                                      pyf.Parameter(name='dim', dtype=pyf.default_integer, value='100')],
                              args=[pyf.Argument(name='arg', dtype=pyf.RealType('FOO')),
                                    pyf.Argument(name='array', dtype=pyf.RealType('FOO'), dimension=('dim', 'dim'))],
                              return_type=pyf.RealType('FOO'))
    param_func_wrapped = fc_wrap.FunctionWrapper(name='param_func_c', wrapped=param_func)
    buf = CodeBuffer()
    param_func_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
    wrapped = '''\
    function param_func_c(arg, array_d1, array_d2, array) bind(c, name="param_func_c")
        use fwrap_ktp_mod
        implicit none
        real(fwrap_FOO) :: arg
        integer(fwrap_default_integer), intent(in) :: array_d1
        integer(fwrap_default_integer), intent(in) :: array_d2
        real(fwrap_FOO), dimension(array_d1, array_d2) :: array
        interface
            function param_func(arg, array)
                use fwrap_ktp_mod
                implicit none

            end function param_func
        end interface

        param_func_c = param_func(arg, array)
    end function param_func_c
'''
    # compare(

def test_declaration_order():
    arr_arg = pyf.Subroutine(name='arr_arg',
                        args=[
                            pyf.Argument('explicit_shape', pyf.default_complex, 'out', dimension=('d1', 'd2')),
                            pyf.Argument('d2', pyf.default_integer, 'in'),
                            pyf.Argument('d1', pyf.default_integer, 'in'),
                            ]
                        )
    iface = '''\
    interface
        subroutine arr_arg(explicit_shape, d2, d1)
            use fwrap_ktp_mod
            implicit none
            integer(fwrap_default_integer), intent(in) :: d2
            integer(fwrap_default_integer), intent(in) :: d1
            complex(fwrap_default_complex), dimension(d1, d2), intent(out) :: explicit_shape
        end subroutine arr_arg
    end interface
'''
    buf = CodeBuffer()
    fc_wrap.generate_interface(arr_arg, fc_wrap.KTP_MOD_NAME, buf)
    compare(iface, buf.getvalue())
 
class test_array_arg_wrapper(object):

    def setup(self):
        self.real_arr_arg = pyf.Argument('real_arr_arg', pyf.default_real, dimension=(':',':',':'), intent='out')
        self.int_arr_arg = pyf.Argument('arr_arg', pyf.default_integer, dimension=(':',':'), intent='inout')
        self.int_arr_wrapper = fc_wrap.ArrayArgWrapper(self.int_arr_arg)
        self.real_arr_wrapper = fc_wrap.ArrayArgWrapper(self.real_arr_arg)

        self.real_explicit_arg = pyf.Argument('real_exp_arg', pyf.default_real, dimension=('d1', 'd2', 'd3'), intent='inout')

    def test_extern_decls(self):
        int_decls = '''\
integer(fwrap_default_integer), intent(in) :: arr_arg_d1
integer(fwrap_default_integer), intent(in) :: arr_arg_d2
integer(fwrap_default_integer), dimension(arr_arg_d1, arr_arg_d2), intent(inout) :: arr_arg
'''
        real_decls = '''\
integer(fwrap_default_integer), intent(in) :: real_arr_arg_d1
integer(fwrap_default_integer), intent(in) :: real_arr_arg_d2
integer(fwrap_default_integer), intent(in) :: real_arr_arg_d3
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
        self.int_arg_wrap = fc_wrap.ArgWrapperFactory(self.int_arg)

        self.lgcl_arg = pyf.Argument(name='lgcl', dtype=dlgcl, intent='inout')
        self.lgcl_arg_wrap = fc_wrap.ArgWrapperFactory(self.lgcl_arg)

        self.lgcl_arg_in = pyf.Argument(name='lgcl_in', dtype=dlgcl, intent='in')
        self.lgcl_arg_in_wrap = fc_wrap.ArgWrapperFactory(self.lgcl_arg_in)

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

class test_arg_wrapper_manager(object):
    
    def setup(self):
        dlgcl = pyf.default_logical
        dint = pyf.IntegerType(ktp='int')
        self.lgcl1 = pyf.Argument(name='lgcl1', dtype=dlgcl, intent='inout')
        self.lgcl2 = pyf.Argument(name='lgcl2', dtype=dlgcl, intent='inout')
        self.intarg = pyf.Argument(name='int', dtype=dint, intent='inout')
        self.args = [self.lgcl1, self.lgcl2, self.intarg]
        self.l1wrap = fc_wrap.ArgWrapper(self.lgcl1)
        self.l2wrap = fc_wrap.ArgWrapper(self.lgcl2)
        self.am = fc_wrap.ArgWrapperManager(self.args)

    def test_arg_declarations(self):
        decls = '''\
logical(fwrap_default_logical), intent(inout) :: lgcl1
logical(fwrap_default_logical), intent(inout) :: lgcl2
integer(fwrap_int), intent(inout) :: int
'''.splitlines()
        eq_(self.am.arg_declarations(), decls)

    def _test_arg_declarations_convert(self):
        decls = '''\
integer(fwrap_default_integer), intent(inout) :: lgcl1
integer(fwrap_default_integer), intent(inout) :: lgcl2
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

class test_arg_manager_return(object):

    def setup(self):
        dlgcl = pyf.default_logical
        dint = pyf.IntegerType(ktp='int')
        self.lgcl = pyf.Argument(name='ll', dtype=dlgcl, intent='out', is_return_arg=True)
        self.int = pyf.Argument(name='int', dtype=dint, intent='out', is_return_arg=True)
        self.am_lgcl = fc_wrap.ArgWrapperManager([], self.lgcl)
        self.am_int = fc_wrap.ArgWrapperManager([], self.int)

    def test_declarations(self):
        declaration = '''\
logical(fwrap_default_logical) :: ll
'''.splitlines()
        eq_(self.am_lgcl.arg_declarations(), declaration)

    def test_temp_declarations(self):
        eq_(self.am_lgcl.temp_declarations(), [])

class test_c_proto_generation(object):
    
    def test_c_proto_args(self):
        args = [pyf.Argument(name='int_arg', dtype=pyf.default_integer, intent='in'),
                pyf.Argument(name='real_arg',dtype=pyf.default_real,    intent='out')]
        return_type = pyf.Argument(name='fname', dtype=pyf.default_real, intent='out', is_return_arg=True)
        arg_man = fc_wrap.ArgWrapperManager(args, return_type)
        eq_(arg_man.c_proto_args(), ['fwrap_default_integer *int_arg', 'fwrap_default_real *real_arg'])

    def test_c_proto_array_args(self):
        args = [pyf.Argument(name='array', dtype=pyf.default_real, dimension=(':',)*3, intent='out')]
        arg_man = fc_wrap.ArgWrapperManager(args)
        eq_(arg_man.c_proto_args(), ['fwrap_default_integer *array_d1',
                                     'fwrap_default_integer *array_d2',
                                     'fwrap_default_integer *array_d3',
                                     'fwrap_default_real *array'])

    def test_c_proto_return_type(self):
        for dtype in (pyf.default_real, pyf.default_integer):
            return_arg = pyf.Argument(name='ret_arg', dtype=dtype, is_return_arg=True)
            am = fc_wrap.ArgWrapperManager([], return_arg)
            eq_(am.c_proto_return_type(), dtype.ktp)

        am_subr = fc_wrap.ArgWrapperManager([])
        eq_(am_subr.c_proto_return_type(), 'void')

    def test_c_prototype_empty(self):
        empty_func = pyf.Function(name='empty_func',
                          args=(),
                          return_type=pyf.default_integer)
        empty_func_wrapper = fc_wrap.FunctionWrapper(name='empty_func_c', wrapped=empty_func)
        eq_(empty_func_wrapper.c_prototype(), 'fwrap_default_integer empty_func_c();')
        empty_subr = pyf.Subroutine(name='empty_subr',
                            args=())
        empty_subr_wrapper = fc_wrap.SubroutineWrapper(name='empty_subr_c', wrapped=empty_subr)
        eq_(empty_subr_wrapper.c_prototype(), 'void empty_subr_c();')

    def test_c_prototype_args(self):
        args = [pyf.Argument(name='int_arg', dtype=pyf.default_integer, intent='in'),
                pyf.Argument(name='array', dtype=pyf.default_real, dimension=(':',)*3, intent='out')]
        func = pyf.Function(name='func', args=args, return_type=pyf.default_integer)
        func_wrapper = fc_wrap.FunctionWrapper(name='func_c', wrapped=func)
        eq_(func_wrapper.c_prototype(), "fwrap_default_integer func_c("
                                        "fwrap_default_integer *int_arg, "
                                        "fwrap_default_integer *array_d1, "
                                        "fwrap_default_integer *array_d2, "
                                        "fwrap_default_integer *array_d3, "
                                        "fwrap_default_real *array);")


# many_arrays_text#{{{
many_arrays_text = '''\
subroutine arr_args_c(assumed_size_d1, assumed_size_d2, assumed_size, d1, assumed_shape_d1, assumed_shape_d2, assumed_shape, explicit_shape_d1, explicit_shape_d2, explicit_shape, c1, c2) bind(c, name="arr_args_c")
    use fwrap_ktp_mod
    implicit none
    integer(fwrap_default_integer), intent(in) :: assumed_size_d1
    integer(fwrap_default_integer), intent(in) :: assumed_size_d2
    integer(fwrap_default_integer), dimension(assumed_size_d1, assumed_size_d2), intent(inout) :: assumed_size
    integer(fwrap_default_integer), intent(in) :: d1
    integer(fwrap_default_integer), intent(in) :: assumed_shape_d1
    integer(fwrap_default_integer), intent(in) :: assumed_shape_d2
    logical(fwrap_default_logical), dimension(assumed_shape_d1, assumed_shape_d2), intent(out) :: assumed_shape
    integer(fwrap_default_integer), intent(in) :: explicit_shape_d1
    integer(fwrap_default_integer), intent(in) :: explicit_shape_d2
    complex(fwrap_default_complex), dimension(explicit_shape_d1, explicit_shape_d2), intent(inout) :: explicit_shape
    integer(fwrap_default_integer), intent(inout) :: c1
    integer(fwrap_default_integer) :: c2
    interface
        subroutine arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
            use fwrap_ktp_mod
            implicit none
            integer(fwrap_default_integer), intent(in) :: d1
            logical(fwrap_default_logical), dimension(:, :), intent(out) :: assumed_shape
            integer(fwrap_default_integer), intent(inout) :: c1
            integer(fwrap_default_integer) :: c2
            integer(fwrap_default_integer), dimension(d1, *), intent(inout) :: assumed_size
            complex(fwrap_default_complex), dimension(c1, c2), intent(inout) :: explicit_shape
        end subroutine arr_args
    end interface
    call arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
end subroutine arr_args_c
'''
#}}}

#---------------- vvv Ignored tests, possibly remove vvv -----------------#{{{

if 0:
    def _test_assumed_size_real_array():
        pass

    def _test_assumed_size_complex_array():
        pass

    def _test_assumed_size_logical_array():
        pass

    def _test_assumed_size_character_array():
        pass


    def _test_character_iface():
        pass

    def _test_logical_function_convert():
        lgcl_fun = pyf.Function(name='lgcl_fun', args=[],
                                return_type=pyf.LogicalType(ktp='lgcl'))
        lgcl_fun_wrapped = fc_wrap.FunctionWrapper(name='lgcl_fun_c', wrapped=lgcl_fun)
        buf = CodeBuffer()
        lgcl_fun_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
        fort_file = '''\
        function lgcl_fun_c() bind(c, name="lgcl_fun_c")
            use fwrap_ktp_mod
            implicit none
            integer(fwrap_default_integer) :: lgcl_fun_c
            interface
                function lgcl_fun()
                    use fwrap_ktp_mod
                    implicit none
                    logical(fwrap_lgcl) :: lgcl_fun
                end function lgcl_fun
            end interface
            logical(fwrap_lgcl) :: lgcl_fun_c_tmp
            lgcl_fun_c_tmp = lgcl_fun()
            if(lgcl_fun_c_tmp) then
                lgcl_fun_c = 1
            else
                lgcl_fun_c = 0
            end if
        end function lgcl_fun_c
    '''
        compare(fort_file, buf.getvalue())

    def _test_logical_wrapper_convert():
        lgcl_arg = pyf.Subroutine(name='lgcl_arg',
                               args=[pyf.Argument(name='lgcl',
                                                  dtype=pyf.LogicalType(ktp='lgcl_ktp'),
                                                  intent="inout")])
        lgcl_arg_wrapped = fc_wrap.SubroutineWrapper(name='lgcl_arg_c', wrapped=lgcl_arg)
        buf = CodeBuffer()
        lgcl_arg_wrapped.generate_wrapper(fc_wrap.KTP_MOD_NAME, buf)
        fort_file = '''\
        subroutine lgcl_arg_c(lgcl) bind(c, name="lgcl_arg_c")
            use fwrap_ktp_mod
            implicit none
            integer(fwrap_default_integer), intent(inout) :: lgcl
            interface
                subroutine lgcl_arg(lgcl)
                    use fwrap_ktp_mod
                    implicit none
                    logical(fwrap_lgcl_ktp), intent(inout) :: lgcl
                end subroutine lgcl_arg
            end interface
            logical(fwrap_lgcl_ktp) :: lgcl_tmp
            if(lgcl .ne. 0) then
                lgcl_tmp = .true.
            else
                lgcl_tmp = .false.
            end if
            call lgcl_arg(lgcl_tmp)
            if(lgcl_tmp) then
                lgcl = 1
            else
                lgcl = 0
            end if
        end subroutine lgcl_arg_c
    '''
        compare(fort_file, buf.getvalue())

    def _test_proc_argument_iface():
        passed_subr = pyf.Subroutine(name='passed_subr',
                           args=[pyf.Argument(name='arg1',
                                              dtype=pyf.default_integer,
                                              intent='inout')])

        proc_arg_func = pyf.Function(name='proc_arg_func',
                             args=[pyf.ProcArgument(passed_subr)],
                             return_type=pyf.default_integer)

        proc_arg_iface = '''\
        interface
            function proc_arg_func(passed_subr)
                use fwrap_ktp_mod
                implicit none
                interface
                    subroutine passed_subr(arg1)
                        use fwrap_ktp_mod
                        implicit none
                        integer(fwrap_default_integer), intent(inout) :: arg1
                    end subroutine passed_subr
                end interface
                integer(fwrap_default_integer) :: proc_arg_func
            end function proc_arg_func
        end interface
    '''
        buf = CodeBuffer()
        fc_wrap.generate_interface(proc_arg_func, fc_wrap.KTP_MOD_NAME, buf)
        compare(proc_arg_iface, buf.getvalue())

#---------------- ^^^ Ignored tests, possibly remove ^^^ -----------------#}}}
