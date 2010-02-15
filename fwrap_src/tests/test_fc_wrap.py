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
    one_arg = pyf.Subroutine(name='one_arg',
                           args=[pyf.Argument(var=pyf.Var(name='a',
                                                          dtype=pyf.Dtype(type='integer', ktp='fwrap_default_int')),
                                      intent="in")])
    one_arg_wrapped = pyf.WrappedSubroutine(name='one_arg_c',
                            args=[pyf.Argument(var=pyf.Var(name='a',
                                                           dtype=pyf.Dtype(type='integer', ktp='fwrap_default_int')),
                                      intent="in")],
                            wrapped=one_arg)
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
                      return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
    empty_func_wrapper = pyf.WrappedFunction(name='empty_func_c',
                      args=(),
                      wrapped=empty_func,
                      return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
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

def test_procedure_argument_iface():
    passed_subr = pyf.Subroutine(name='passed_subr',
                       args=[pyf.Argument(pyf.Var(name='arg1',
                                                  dtype=pyf.Dtype(type='integer', ktp='fwrap_default_int')),
                                  intent='inout')])

    proc_arg_func = pyf.Function(name='proc_arg_func',
                         args=[pyf.ProcArgument(passed_subr)],
                         return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))

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

def test_gen_iface():

    def gen_iface_gen(ast, istr):
        buf = CodeBuffer()
        fc_wrap.FortranInterfaceGen(buf).generate(ast)
        compare(istr, buf.getvalue())


    many_arg_subr = pyf.Subroutine(name='many_arg_subr',
                         args=[pyf.Argument(pyf.Var(name='arg1',
                                                    dtype=pyf.Dtype(type='complex', ktp='fwrap_sik_10_20')),
                                            intent='in'),
                               pyf.Argument(pyf.Var(name='arg2',
                                                    dtype=pyf.Dtype(type='real', ktp='fwrap_double_precision')),
                                            intent='inout'),
                               pyf.Argument(pyf.Var(name='arg3',
                                                    dtype=pyf.Dtype(type='integer', ktp='fwrap_int_x_8')),
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
                        args=[pyf.Argument(pyf.Var(name='arg1',
                                                  dtype=pyf.Dtype(type='real', ktp='fwrap_default_real')),
                                           intent='inout')],
                        return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
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
                      return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
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

def test_logical_wrapper():
    lgcl_arg = pyf.Subroutine(name='lgcl_arg',
                           args=[pyf.Argument(pyf.Var(name='lgcl',
                                                      dtype=pyf.Dtype(type='logical', ktp='fwrap_lgcl_ktp')),
                                              intent="inout")])
    lgcl_arg_wrapped = pyf.WrappedSubroutine(name='lgcl_arg_c',
                            args=[pyf.Argument(pyf.Var(name='lgcl',
                                                       dtype=pyf.Dtype(type='logical', ktp='fwrap_lgcl_ktp')),
                                              intent="inout")],
                            wrapped=lgcl_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_arg_wrapped)
    fort_file = '''\
    subroutine lgcl_arg_c(lgcl) bind(c, name="lgcl_arg_c")
        use config
        implicit none
        integer(fwrap_int_ktp), intent(inout) :: lgcl
        interface
            subroutine lgcl_arg(lgcl)
                use config
                implicit none
                logical(fwrap_lgcl_ktp), intent(inout) :: lgcl
            end subroutine lgcl_arg
        end interface
        logical(fwrap_lgcl_ktp) :: lgcl_tmp
        if(lgcl .ne. 1) then
            lgcl_tmp = .true.
        else
            lgcl_tmp = .false.
        end if
        call lgcl_arg(lgcl_tmp)
        if(lgcl_tmp) then
            lgcl = 1
        else
            lgcl = 0
        endif
    end subroutine lgcl_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_character_iface():
    pass

def _test_assumed_size_int_array():
    arr_arg = pyf.Subroutine(name='arr_arg',
                           args=[pyf.Argument(pyf.Var(name='arr',
                                                      dtype=pyf.Dtype(type='integer', ktp='fwrap_int',
                                                              dimension=[':',':'])),
                                              intent="inout")])
    arr_arg_wrapped = pyf.WrappedSubroutine(name='lgcl_arg_c',
                            args=[pyf.Argument(name='lgcl',
                                      dtype=pyf.Dtype(type='logical', ktp='fwrap_lgcl_ktp'),
                                      intent="inout")],
                            wrapped=lgcl_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_arg_wrapped)
    fort_file = '''\
    subroutine arr_arg_c(arr, arr_d1, arr_d2) bind(c, name="arr_arg_c")
        use config
        implicit none
        integer(fwrap_int), intent(in) :: arr_d1, arr_d2
        integer(fwrap_int), intent(inout), dimension(arr_d1, arr_d2) :: arr
        interface
            subroutine arr_arg(arr)
                use config
                implicit none
                logical(fwrap_int), intent(inout), dimension(:,:) :: arr
            end subroutine arr_arg
        end interface
        call arr_arg(arr)
    end subroutine arr_arg_c
'''
    compare(fort_file, buf.getvalue())
    yield fcompile, fort_file

def test_assumed_size_real_array():
    pass

def test_assumed_size_complex_array():
    pass

def test_assumed_size_logical_array():
    pass

def test_assumed_size_character_array():
    pass
