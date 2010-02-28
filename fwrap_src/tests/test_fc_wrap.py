from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

def remove_common_indent(s):
    ws_count = 0
    fst_line = s.splitlines()[0]
    for ch in fst_line:
        if ch == ' ':
            ws_count += 1
        else:
            break

    if not ws_count: return s

    ret = []
    for line in s.splitlines():
        if line:
            assert line[:ws_count] == ' '*ws_count
            ret.append(line[ws_count:])
        else:
            ret.append('')
    return '\n'.join(ret)

def compare(s1, s2):
    ss1 = remove_common_indent(s1.rstrip())
    ss2 = remove_common_indent(s2.rstrip())
    eq_(ss1, ss2, msg='\n%s\n != \n%s' % (ss1, ss2))

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
fwrap_default_int empty_func_c();
'''.splitlines()
        eq_(header_file, self.buf.getvalue().splitlines())

    def test_generate_pxd_empty_func(self):
        pname = "DP"
        fc_wrap.GenPxd(pname).generate([self.empty_func], self.buf)
        pxd_file = '''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''.splitlines()
        eq_(pxd_file, self.buf.getvalue().splitlines())

def test_gen_fortran_one_arg_func():
    one_arg = pyf.Subroutine(
            name='one_arg',
            args=[pyf.Argument(name='a',
                               dtype=pyf.default_integer,
                               intent="in")])
    one_arg_wrapped = pyf.SubroutineWrapper(name='one_arg_c', wrapped=one_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(one_arg_wrapped)
    fort_file = '''\
    subroutine one_arg_c(a) bind(c, name="one_arg_c")
        use config
        implicit none
        integer(fwrap_default_int), intent(in) :: a
        interface
            subroutine one_arg(a)
                use config
                implicit none
                integer(fwrap_default_int), intent(in) :: a
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
    empty_func_wrapper = pyf.FunctionWrapper(name='empty_func_c', wrapped=empty_func)
                      
    empty_func_wrapped = '''\
    function empty_func_c() bind(c, name="empty_func_c")
        use config
        implicit none
        integer(fwrap_default_int) :: empty_func_c
        interface
            function empty_func()
                use config
                implicit none
                integer(fwrap_default_int) :: empty_func
            end function empty_func
        end interface
        empty_func_c = empty_func()
    end function empty_func_c
'''
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(empty_func_wrapper)
    compare(empty_func_wrapped, buf.getvalue())

def test_gen_iface():

    def gen_iface_gen(ast, istr):
        buf = CodeBuffer()
        fc_wrap.FortranInterfaceGen(buf).generate(ast)
        compare(istr, buf.getvalue())


    many_arg_subr = pyf.Subroutine(name='many_arg_subr',
                         args=[pyf.Argument(name='arg1',
                                            dtype=pyf.ComplexType('fwrap_sik_10_20'),
                                            intent='in'),
                               pyf.Argument(name='arg2',
                                            dtype=pyf.RealType('fwrap_double_precision'),
                                            intent='inout'),
                               pyf.Argument(name='arg3',
                                            dtype=pyf.IntegerType('fwrap_int_x_8'),
                                            intent='out')])
    many_arg_subr_iface = '''\
    interface
        subroutine many_arg_subr(arg1, arg2, arg3)
            use config
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
            use config
            implicit none
            real(fwrap_default_real), intent(inout) :: arg1
            integer(fwrap_default_int) :: one_arg_func
        end function one_arg_func
    end interface
'''

    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_type=pyf.default_integer)
    empty_func_iface = '''\
    interface
        function empty_func()
            use config
            implicit none
            integer(fwrap_default_int) :: empty_func
        end function empty_func
    end interface
'''
    data = [(many_arg_subr, many_arg_subr_iface),
            (one_arg_func, one_arg_func_iface),
            (empty_func, empty_func_iface)]

    for ast, iface in data:
        yield gen_iface_gen, ast, iface

def test_logical_function():
    lgcl_fun = pyf.Function(name='lgcl_fun', args=[],
                            return_type=pyf.LogicalType(ktp='fwrap_lgcl'))
    lgcl_fun_wrapped = pyf.FunctionWrapper(name='lgcl_fun_c', wrapped=lgcl_fun)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_fun_wrapped)
    fort_file = '''\
    function lgcl_fun_c() bind(c, name="lgcl_fun_c")
        use config
        implicit none
        logical(fwrap_lgcl) :: lgcl_fun_c
        interface
            function lgcl_fun()
                use config
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
                                              dtype=pyf.LogicalType(ktp='fwrap_lgcl_ktp'),
                                              intent="inout")])
    lgcl_arg_wrapped = pyf.SubroutineWrapper(name='lgcl_arg_c', wrapped=lgcl_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_arg_wrapped)
    fort_file = '''\
    subroutine lgcl_arg_c(lgcl) bind(c, name="lgcl_arg_c")
        use config
        implicit none
        logical(fwrap_lgcl_ktp), intent(inout) :: lgcl
        interface
            subroutine lgcl_arg(lgcl)
                use config
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
    arr_arg_wrapped = pyf.SubroutineWrapper(name='arr_arg_c', wrapped=arr_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(arr_arg_wrapped)
    fort_file = '''\
    subroutine arr_arg_c(arr_d1, arr_d2, arr) bind(c, name="arr_arg_c")
        use config
        implicit none
        integer(fwrap_default_int), intent(in) :: arr_d1
        integer(fwrap_default_int), intent(in) :: arr_d2
        integer(fwrap_default_int), dimension(arr_d1, arr_d2), intent(inout) :: arr
        interface
            subroutine arr_arg(arr)
                use config
                implicit none
                integer(fwrap_default_int), dimension(:, :), intent(inout) :: arr
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
    arr_arg_wrapped = pyf.SubroutineWrapper(name='arr_arg_c', wrapped=arr_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(arr_arg_wrapped)
    fort_file = '''\
    subroutine arr_arg_c(arr_d1, arr_d2, arr, d1, d2) bind(c, name="arr_arg_c")
        use config
        implicit none
        integer(fwrap_default_int), intent(in) :: arr_d1
        integer(fwrap_default_int), intent(in) :: arr_d2
        integer(fwrap_default_int), dimension(arr_d1, arr_d2), intent(inout) :: arr
        integer(fwrap_default_int), intent(in) :: d1
        integer(fwrap_default_int), intent(in) :: d2
        interface
            subroutine arr_arg(arr, d1, d2)
                use config
                implicit none
                integer(fwrap_default_int), intent(in) :: d1
                integer(fwrap_default_int), intent(in) :: d2
                integer(fwrap_default_int), dimension(d1, d2), intent(inout) :: arr
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
    arr_args_wrapped = pyf.SubroutineWrapper(name='arr_args_c', wrapped=arr_args)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(arr_args_wrapped)
    compare(many_arrays_text, buf.getvalue())

def _test_declaration_order():
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
            use config
            implicit none
            integer(fwrap_default_int), intent(in) :: d1
            integer(fwrap_default_int), intent(in) :: d2
            complex(fwrap_default_complex), dimension(d1, d2), intent(out) :: explicit_shape
        end subroutine arr_arg
    end interface
'''
    buf = CodeBuffer()
    fc_wrap.FortranInterfaceGen(buf).generate(arr_arg)
    compare(iface, buf.getvalue())

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
                            return_type=pyf.LogicalType(ktp='fwrap_lgcl'))
    lgcl_fun_wrapped = pyf.FunctionWrapper(name='lgcl_fun_c', wrapped=lgcl_fun)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_fun_wrapped)
    fort_file = '''\
    function lgcl_fun_c() bind(c, name="lgcl_fun_c")
        use config
        implicit none
        integer(fwrap_default_int) :: lgcl_fun_c
        interface
            function lgcl_fun()
                use config
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
                                              dtype=pyf.LogicalType(ktp='fwrap_lgcl_ktp'),
                                              intent="inout")])
    lgcl_arg_wrapped = pyf.SubroutineWrapper(name='lgcl_arg_c', wrapped=lgcl_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_arg_wrapped)
    fort_file = '''\
    subroutine lgcl_arg_c(lgcl) bind(c, name="lgcl_arg_c")
        use config
        implicit none
        integer(fwrap_default_int), intent(inout) :: lgcl
        interface
            subroutine lgcl_arg(lgcl)
                use config
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

many_arrays_text = '''\
subroutine arr_args_c(assumed_size_d1, assumed_size_d2, assumed_size, d1, assumed_shape_d1, assumed_shape_d2, assumed_shape, explicit_shape_d1, explicit_shape_d2, explicit_shape, c1, c2) bind(c, name="arr_args_c")
    use config
    implicit none
    integer(fwrap_default_int), intent(in) :: assumed_size_d1
    integer(fwrap_default_int), intent(in) :: assumed_size_d2
    integer(fwrap_default_int), dimension(assumed_size_d1, assumed_size_d2), intent(inout) :: assumed_size
    integer(fwrap_default_int), intent(in) :: d1
    integer(fwrap_default_int), intent(in) :: assumed_shape_d1
    integer(fwrap_default_int), intent(in) :: assumed_shape_d2
    logical(fwrap_default_logical), dimension(assumed_shape_d1, assumed_shape_d2), intent(out) :: assumed_shape
    integer(fwrap_default_int), intent(in) :: explicit_shape_d1
    integer(fwrap_default_int), intent(in) :: explicit_shape_d2
    complex(fwrap_default_complex), dimension(explicit_shape_d1, explicit_shape_d2), intent(inout) :: explicit_shape
    integer(fwrap_default_int), intent(inout) :: c1
    integer(fwrap_default_int) :: c2
    interface
        subroutine arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
            use config
            implicit none
            integer(fwrap_default_int), intent(in) :: d1
            logical(fwrap_default_logical), dimension(:, :), intent(out) :: assumed_shape
            integer(fwrap_default_int), intent(inout) :: c1
            integer(fwrap_default_int) :: c2
            integer(fwrap_default_int), dimension(d1, *), intent(inout) :: assumed_size
            complex(fwrap_default_complex), dimension(c1, c2), intent(inout) :: explicit_shape
        end subroutine arr_args
    end interface
    call arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
end subroutine arr_args_c
'''

def _test_procedure_argument_iface():
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
            use config
            implicit none
            interface
                subroutine passed_subr(arg1)
                    use config
                    implicit none
                    integer(fwrap_default_int), intent(inout) :: arg1
                end subroutine passed_subr
            end interface
            integer(fwrap_default_int) :: proc_arg_func
        end function proc_arg_func
    end interface
'''
    buf = CodeBuffer()
    fc_wrap.FortranInterfaceGen(buf).generate(proc_arg_func)
    compare(proc_arg_iface, buf.getvalue())

