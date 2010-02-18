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
                      return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
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

def test_logical_function():
    lgcl_fun = pyf.Function(name='lgcl_fun', args=[],
                            return_type=pyf.Dtype(type='logical', ktp='fwrap_lgcl'))
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

def test_logical_wrapper():
    lgcl_arg = pyf.Subroutine(name='lgcl_arg',
                           args=[pyf.Argument(pyf.Var(name='lgcl',
                                                      dtype=pyf.Dtype(type='logical', ktp='fwrap_lgcl_ktp')),
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


def _test_assumed_shape_int_array():
    arr_arg = pyf.Subroutine(name='arr_arg',
                           args=[pyf.Argument(pyf.Var(name='arr',
                                                      dtype=pyf.Dtype(type='integer', ktp='fwrap_int',
                                                              dimension=[':',':'])),
                                              intent="inout")])
    arr_arg_wrapped = pyf.SubroutineWrapper(name='lgcl_arg_c', wrapped=lgcl_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_arg_wrapped)
    fort_file = '''\
    subroutine arr_arg_c(arr, arr_d1, arr_d2) bind(c, name="arr_arg_c")
        use config
        implicit none
        integer(fwrap_int), intent(in) :: arr_d1
        integer(fwrap_int), intent(in) :: arr_d2
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

def _test_explicit_shape_int_array():
    arr_arg = pyf.Subroutine(name='arr_arg',
                           args=[pyf.Argument(pyf.Var(name='arr',
                                                      dtype=pyf.Dtype(type='integer', ktp='fwrap_int',
                                                              dimension=['10','20'])),
                                              intent="inout")])
    arr_arg_wrapped = pyf.SubroutineWrapper(name='arr_arg_c', wrapped=arr_arg)
    buf = CodeBuffer()
    fc_wrap.FortranWrapperGen(buf).generate(lgcl_arg_wrapped)
    fort_file = '''\
    subroutine arr_arg_c(arr, arr_d1, arr_d2) bind(c, name="arr_arg_c")
        use config
        implicit none
        integer(fwrap_int), intent(in) :: arr_d1, arr_d2
        integer(fwrap_int), intent(inout), dimension(arr_d1, arr_d2) :: arr
        interface
            subroutine arr_arg(d1, d2, arr)
                use config
                implicit none
                integer(fwrap_int), intent(in) :: d1
                integer(fwrap_int), intent(in) :: d2
                logical(fwrap_int), intent(inout), dimension(d1, d2) :: arr
            end subroutine arr_arg
        end interface
        call arr_arg(arr_d1, arr_d2, arr)
    end subroutine arr_arg_c
'''
    compare(fort_file, buf.getvalue())

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

class test_arg_wrapper(object):

    def setup(self):
        dint = pyf.Dtype(type='integer', ktp='fwrap_int')
        dlgcl = pyf.Dtype(type='logical', ktp='fwrap_default_logical')

        self.int_arg = pyf.Argument(pyf.Var(name='int', dtype=dint),
                                    intent='inout')
        self.int_arg_wrap = pyf.ArgWrapper(self.int_arg)

        self.lgcl_arg = pyf.Argument(var=pyf.Var(name='lgcl', dtype=dlgcl),
                                     intent='inout')
        self.lgcl_arg_wrap = pyf.LogicalWrapper(self.lgcl_arg)

        self.lgcl_arg_in = pyf.Argument(var=pyf.Var(name='lgcl_in', dtype=dlgcl),
                                        intent='in')
        self.lgcl_arg_in_wrap = pyf.LogicalWrapper(self.lgcl_arg_in)

    def test_extern_int_arg(self):
        eq_(self.int_arg_wrap.extern_arg.declaration(), self.int_arg.declaration())

    def test_intern_int_var(self):
        eq_(self.int_arg_wrap.intern_var, None)

    def test_pre_call_code_int(self):
        eq_(self.int_arg_wrap.pre_call_code(), None)

    def test_post_call_code_int(self):
        eq_(self.int_arg_wrap.post_call_code(), None)

    def test_extern_lgcl_arg(self):
        eq_(self.lgcl_arg_wrap.extern_arg.declaration(),
                'integer(fwrap_default_int), intent(inout) :: lgcl')
        eq_(self.lgcl_arg_in_wrap.extern_arg.declaration(),
                'integer(fwrap_default_int), intent(in) :: lgcl_in')

    def test_intern_lgcl_var(self):
        eq_(self.lgcl_arg_wrap.intern_var.declaration(),
                'logical(fwrap_default_logical) :: lgcl_tmp')
        eq_(self.lgcl_arg_in_wrap.intern_var.declaration(),
                'logical(fwrap_default_logical) :: lgcl_in_tmp')

    def test_pre_call_code(self):
        for argw in (self.lgcl_arg_wrap, self.lgcl_arg_in_wrap):
            pcc = '''\
if(%(extern_arg)s .ne. 0) then
    %(intern_var)s = .true.
else
    %(intern_var)s = .false.
end if
''' % {'extern_arg' : argw.extern_arg.name,
       'intern_var' : argw.intern_var.name}
            eq_(argw.pre_call_code(), pcc.splitlines())

    def test_post_call_code(self):
        for argw in (self.lgcl_arg_wrap, self.lgcl_arg_in_wrap):
            pcc = '''\
if(%(intern_var)s) then
    %(extern_arg)s = 1
else
    %(extern_arg)s = 0
end if
''' % {'extern_arg' : argw.extern_arg.name,
       'intern_var' : argw.intern_var.name}
            eq_(argw.post_call_code(), pcc.splitlines())

class test_arg_manager_return(object):

    def setup(self):
        dlgcl = pyf.Dtype(type='logical', ktp='fwrap_default_logical')
        dint = pyf.Dtype(type='integer', ktp='fwrap_int')
        self.lgcl = pyf.Argument(pyf.Var(name='ll', dtype=dlgcl), intent='out', is_return_arg=True)
        self.int = pyf.Argument(pyf.Var(name='int', dtype=dint), intent='out', is_return_arg=True)
        self.am_lgcl = pyf.ArgManager([], self.lgcl)
        self.am_int = pyf.ArgManager([], self.int)

    def test_declarations(self):
        decl = '''\
integer(fwrap_default_int) :: ll
'''.splitlines()
        eq_(self.am_lgcl.extern_declarations(), decl)

    def test_temp_declarations(self):
        decl = '''\
logical(fwrap_default_logical) :: ll_tmp
'''.splitlines()
        eq_(self.am_lgcl.temp_declarations(), decl)

class test_arg_manager(object):
    
    def setup(self):
        dlgcl = pyf.Dtype(type='logical', ktp='fwrap_default_logical')
        dint = pyf.Dtype(type='integer', ktp='fwrap_int')
        self.lgcl1 = pyf.Argument(pyf.Var(name='lgcl1', dtype=dlgcl), intent='inout')
        self.lgcl2 = pyf.Argument(pyf.Var(name='lgcl2', dtype=dlgcl), intent='inout')
        self.intarg = pyf.Argument(pyf.Var(name='int', dtype=dint), intent='inout')
        self.args = [self.lgcl1, self.lgcl2, self.intarg]
        self.l1wrap = pyf.LogicalWrapper(self.lgcl1)
        self.l2wrap = pyf.LogicalWrapper(self.lgcl2)
        self.am = pyf.ArgManager(self.args)

    def test_arg_declarations(self):
        decls = '''\
integer(fwrap_default_int), intent(inout) :: lgcl1
integer(fwrap_default_int), intent(inout) :: lgcl2
integer(fwrap_int), intent(inout) :: int
'''.splitlines()
        eq_(self.am.arg_declarations(), decls)

    def test_temp_declarations(self):
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
        cl = 'lgcl1_tmp lgcl2_tmp int'.split()
        eq_(self.am.call_arg_list(), cl)

    #TODO
    def _test_arg_mangle_collision(self):
        # when two passed logical arguments have the name 'lgcl' and 'lgcl_tmp'
        # the intern_var for lgcl can't be named 'lgcl_tmp'
        # this needs to be detected and resolved.
        pass
