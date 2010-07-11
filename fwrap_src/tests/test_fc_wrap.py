from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from fwrap_src.code import CodeBuffer

from tutils import compare

from nose.tools import ok_, eq_, set_trace

def test_generate_fc_h():
    return_arg = pyf.Argument(name="two_arg", dtype=pyf.default_real)
    two_arg_func = pyf.Function(
            name='two_arg',
            args=[pyf.Argument(name='a',dtype=pyf.default_integer,
                                intent='in'),
                  pyf.Argument(name='b', dtype=pyf.default_integer,
                                intent='in'),
                  pyf.Argument(name='c', dtype=pyf.default_integer,
                                intent='in'),
                  pyf.Argument(name='d', dtype=pyf.default_integer,
                                intent='in'),
                  ],
            return_arg=return_arg)
    ta_wrp = fc_wrap.FunctionWrapper(wrapped=two_arg_func)
    ast = [ta_wrp]
    buf = CodeBuffer()
    header_name = 'foobar'
    fc_wrap.generate_fc_h(ast, header_name, buf)
    code = '''\
    #include "foobar"
    
    void two_arg_c(fwrap_default_real *fw_ret_arg, fwrap_default_integer *a, fwrap_default_integer *b, fwrap_default_integer *c, fwrap_default_integer *d, fwrap_default_integer *fw_iserr__);
    '''
    compare(buf.getvalue(), code)

def test_generate_fc_pxd():
    return_arg = pyf.Argument(name="two_arg", dtype=pyf.default_real)
    two_arg_func = pyf.Function(
            name='two_arg',
            args=[pyf.Argument(name='a',dtype=pyf.default_integer,
                                intent='in'),
                  pyf.Argument(name='b', dtype=pyf.default_integer,
                                intent='in')],
            return_arg=return_arg)
    ta_wrp = fc_wrap.FunctionWrapper(wrapped=two_arg_func)
    ast = [ta_wrp]
    buf = CodeBuffer()
    header_name = 'foobar'
    fc_wrap.generate_fc_pxd(ast, header_name, buf)
    code = '''\
    from fwrap_ktp cimport *

    cdef extern from "foobar":
        void two_arg_c(fwrap_default_real *fw_ret_arg, fwrap_default_integer *a, fwrap_default_integer *b, fwrap_default_integer *fw_iserr__)
    '''
    compare(buf.getvalue(), code)


def test_gen_fortran_one_arg_func():
    one_arg = pyf.Subroutine(
            name='one_arg',
            args=[pyf.Argument(name='a',
                               dtype=pyf.default_integer,
                               intent="in")])
    one_arg_wrapped = fc_wrap.SubroutineWrapper(wrapped=one_arg)
    buf = CodeBuffer()
    one_arg_wrapped.generate_wrapper(buf)
    fort_file = '''\
    subroutine one_arg_c(a, fw_iserr__) bind(c, name="one_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_default_integer), intent(in) :: a
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            subroutine one_arg(a)
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_default_integer), intent(in) :: a
            end subroutine one_arg
        end interface
        fw_iserr__ = FW_INIT_ERR__
        call one_arg(a)
        fw_iserr__ = FW_NO_ERR__
    end subroutine one_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_gen_empty_func_wrapper():
    return_arg = pyf.Argument("empty_func", dtype=pyf.default_integer)
    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_arg=return_arg)
    empty_func_wrapper = fc_wrap.FunctionWrapper(wrapped=empty_func)
                      
    empty_func_wrapped = '''\
    subroutine empty_func_c(fw_ret_arg, fw_iserr__) bind(c, name="empty_func_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_default_integer), intent(out) :: fw_ret_arg
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            function empty_func()
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_default_integer) :: empty_func
            end function empty_func
        end interface
        fw_iserr__ = FW_INIT_ERR__
        fw_ret_arg = empty_func()
        fw_iserr__ = FW_NO_ERR__
    end subroutine empty_func_c
'''
    buf = CodeBuffer()
    empty_func_wrapper.generate_wrapper(buf)
    compare(empty_func_wrapped, buf.getvalue())

def test_gen_iface():

    def gen_iface_gen(ast, istr):
        buf = CodeBuffer()
        #ast.generate_interface(buf)
        fc_wrap.generate_interface(ast, buf)
        compare(istr, buf.getvalue())


    args=[pyf.Argument(name='arg1',
                       dtype=pyf.ComplexType('sik_10_20'),
                       intent='in'),
          pyf.Argument(name='arg2',
                       dtype=pyf.RealType('double_precision'),
                       intent='inout'),
          pyf.Argument(name='arg3',
                       dtype=pyf.IntegerType('int_x_8'),
                       intent='out')]
    many_arg_subr = pyf.Subroutine(
                        name='many_arg_subr',
                        args=args)
    many_arg_subr_iface = '''\
    interface
        subroutine many_arg_subr(arg1, arg2, arg3)
            use fwrap_ktp_mod
            implicit none
            complex(kind=fwrap_sik_10_20), intent(in) :: arg1
            real(kind=fwrap_double_precision), intent(inout) :: arg2
            integer(kind=fwrap_int_x_8), intent(out) :: arg3
        end subroutine many_arg_subr
    end interface
'''

    return_arg = pyf.Argument(name="one_arg_func", dtype=pyf.default_integer)
    one_arg_func = pyf.Function(name='one_arg_func',
                        args=[pyf.Argument(name='arg1',
                                           dtype=pyf.default_real,
                                           intent='inout')],
                        return_arg=return_arg)
    one_arg_func_iface = '''\
    interface
        function one_arg_func(arg1)
            use fwrap_ktp_mod
            implicit none
            real(kind=fwrap_default_real), intent(inout) :: arg1
            integer(kind=fwrap_default_integer) :: one_arg_func
        end function one_arg_func
    end interface
'''

    return_arg = pyf.Argument(name="one_arg_func", dtype=pyf.default_integer)
    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_arg=return_arg)
    empty_func_iface = '''\
    interface
        function empty_func()
            use fwrap_ktp_mod
            implicit none
            integer(kind=fwrap_default_integer) :: empty_func
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
    wppr = fc_wrap.SubroutineWrapper(wrapped=hide_arg_subr)
    buf = CodeBuffer()
    wppr.generate_wrapper(buf)
    check = '''\
    subroutine hide_subr_c(fw_iserr__) bind(c, name="hide_subr_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            subroutine hide_subr(hide_arg)
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_default_integer) :: hide_arg
            end subroutine hide_subr
        end interface
        integer(kind=fwrap_default_integer) :: hide_arg
        fw_iserr__ = FW_INIT_ERR__
        hide_arg = (10)
        call hide_subr(hide_arg)
        fw_iserr__ = FW_NO_ERR__
    end subroutine hide_subr_c
'''
    compare(check, buf.getvalue())

def test_logical_function():
    return_arg = pyf.Argument('lgcl_fun', 
            dtype=pyf.LogicalType(fw_ktp='lgcl'))
    lgcl_fun = pyf.Function(name='lgcl_fun', args=[],
                            return_arg=return_arg)
    lgcl_fun_wrapped = fc_wrap.FunctionWrapper(wrapped=lgcl_fun)
    buf = CodeBuffer()
    lgcl_fun_wrapped.generate_wrapper(buf)
    fort_file = '''\
    subroutine lgcl_fun_c(fw_ret_arg, fw_iserr__) bind(c, name="lgcl_fun_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_lgcl), intent(out) :: fw_ret_arg
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            function lgcl_fun()
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_lgcl) :: lgcl_fun
            end function lgcl_fun
        end interface
        fw_iserr__ = FW_INIT_ERR__
        fw_ret_arg = lgcl_fun()
        fw_iserr__ = FW_NO_ERR__
    end subroutine lgcl_fun_c
'''
    compare(fort_file, buf.getvalue())

def test_logical_wrapper():
    args=[pyf.Argument(name='lgcl',
                      dtype=pyf.LogicalType(fw_ktp='lgcl_ktp'),
                      intent="inout")]
    lgcl_arg = pyf.Subroutine(name='lgcl_arg', args=args)
    lgcl_arg_wrapped = fc_wrap.SubroutineWrapper(wrapped=lgcl_arg)
    buf = CodeBuffer()
    lgcl_arg_wrapped.generate_wrapper(buf)
    fort_file = '''\
    subroutine lgcl_arg_c(lgcl, fw_iserr__) bind(c, name="lgcl_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_lgcl_ktp), intent(inout) :: lgcl
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            subroutine lgcl_arg(lgcl)
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_lgcl_ktp), intent(inout) :: lgcl
            end subroutine lgcl_arg
        end interface
        fw_iserr__ = FW_INIT_ERR__
        call lgcl_arg(lgcl)
        fw_iserr__ = FW_NO_ERR__
    end subroutine lgcl_arg_c
'''
    compare(fort_file, buf.getvalue())


def test_assumed_shape_int_array():
    arr_arg = pyf.Subroutine(name='arr_arg',
                           args=[pyf.Argument(name='arr',
                                              dtype=pyf.default_integer,
                                              dimension=(':',':'),
                                              intent="inout")])
    arr_arg_wrapped = fc_wrap.SubroutineWrapper(wrapped=arr_arg)
    buf = CodeBuffer()
    arr_arg_wrapped.generate_wrapper(buf)
    fort_file = '''\
    subroutine arr_arg_c(arr_d1, arr_d2, arr, fw_iserr__) bind(c, name="arr_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_npy_intp), intent(in) :: arr_d1
        integer(kind=fwrap_npy_intp), intent(in) :: arr_d2
        integer(kind=fwrap_default_integer), dimension(arr_d1, arr_d2), intent(inout) :: arr
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            subroutine arr_arg(arr)
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_default_integer), dimension(:, :), intent(inout) :: arr
            end subroutine arr_arg
        end interface
        fw_iserr__ = FW_INIT_ERR__
        call arr_arg(arr)
        fw_iserr__ = FW_NO_ERR__
    end subroutine arr_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_explicit_shape_int_array():
    args=[pyf.Argument(name='arr',
                       dtype=pyf.default_integer,
                       dimension=('d1', 'd2'),
                       intent="inout"),
          pyf.Argument(name='d1', 
                       dtype=pyf.default_integer,
                       intent='in'),
          pyf.Argument(name='d2', 
                       dtype=pyf.default_integer,
                       intent='in')
        ]
    arr_arg = pyf.Subroutine(name='arr_arg', args=args)
    arr_arg_wrapped = fc_wrap.SubroutineWrapper(wrapped=arr_arg)
    buf = CodeBuffer()
    arr_arg_wrapped.generate_wrapper(buf)
    fort_file = '''\
    subroutine arr_arg_c(arr_d1, arr_d2, arr, d1, d2, fw_iserr__) bind(c, name="arr_arg_c")
        use fwrap_ktp_mod
        implicit none
        integer(kind=fwrap_npy_intp), intent(in) :: arr_d1
        integer(kind=fwrap_npy_intp), intent(in) :: arr_d2
        integer(kind=fwrap_default_integer), dimension(arr_d1, arr_d2), intent(inout) :: arr
        integer(kind=fwrap_default_integer), intent(in) :: d1
        integer(kind=fwrap_default_integer), intent(in) :: d2
        integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
        interface
            subroutine arr_arg(arr, d1, d2)
                use fwrap_ktp_mod
                implicit none
                integer(kind=fwrap_default_integer), intent(in) :: d1
                integer(kind=fwrap_default_integer), intent(in) :: d2
                integer(kind=fwrap_default_integer), dimension(d1, d2), intent(inout) :: arr
            end subroutine arr_arg
        end interface
        fw_iserr__ = FW_INIT_ERR__
        call arr_arg(arr, d1, d2)
        fw_iserr__ = FW_NO_ERR__
    end subroutine arr_arg_c
'''
    compare(fort_file, buf.getvalue())

def test_many_arrays():
    args=[pyf.Argument('assumed_size', 
                pyf.default_integer, "inout", dimension=('d1','*')),
          pyf.Argument('d1', pyf.default_integer, 'in'),
          pyf.Argument('assumed_shape', 
                pyf.default_logical, 'out', dimension=(':', ':')),
          pyf.Argument('explicit_shape', 
                pyf.default_complex, 'inout', ('c1', 'c2')),
          pyf.Argument('c1', pyf.default_integer, 'inout'),
          pyf.Argument('c2', pyf.default_integer)
        ]
    arr_args = pyf.Subroutine(name='arr_args', args=args)
    arr_args_wrapped = fc_wrap.SubroutineWrapper(wrapped=arr_args)
    buf = CodeBuffer()
    arr_args_wrapped.generate_wrapper(buf)
    compare(many_arrays_text, buf.getvalue())

def test_declaration_order():
    args=[
        pyf.Argument('explicit_shape', 
            pyf.default_complex, 'out', dimension=('d1', 'd2')),
        pyf.Argument('d2', pyf.default_integer, 'in'),
        pyf.Argument('d1', pyf.default_integer, 'in'),
        ]
    arr_arg = pyf.Subroutine(name='arr_arg', args=args)
    iface = '''\
    interface
        subroutine arr_arg(explicit_shape, d2, d1)
            use fwrap_ktp_mod
            implicit none
            integer(kind=fwrap_default_integer), intent(in) :: d2
            integer(kind=fwrap_default_integer), intent(in) :: d1
            complex(kind=fwrap_default_complex), dimension(d1, d2), intent(out) :: explicit_shape
        end subroutine arr_arg
    end interface
'''
    buf = CodeBuffer()
    fc_wrap.generate_interface(arr_arg, buf)
    compare(iface, buf.getvalue())

class test_char_array_arg_wrapper(object):

    def setup(self):
        charr1 = pyf.Argument('charr1', 
                              pyf.CharacterType("char_x20",
                                                len="20",
                                                odecl="character(20)"),
                              dimension=(":",),
                              intent="inout")
        charr3 = pyf.Argument('charr3', 
                              pyf.CharacterType("char_x30",
                                                len="30",
                                                odecl="character(30)"),
                              dimension=[':']*3,
                              intent="inout")
        charr_star = pyf.Argument('cs',
                                  pyf.CharacterType("char_xX",
                                                    len="*",
                                                    odecl="character(*)"),
                                  dimension=('n1',),
                                  intent='inout')
        charr_in = pyf.Argument('charrin',
                                pyf.CharacterType("char_in",
                                                  len="20",
                                                  odecl="character(20"),
                                dimension=(":",),
                                intent="in")
        self.fc_charr1 = fc_wrap.CharArrayArgWrapper(charr1)
        self.fc_charr3 = fc_wrap.CharArrayArgWrapper(charr3)
        self.fc_charr_star = fc_wrap.CharArrayArgWrapper(charr_star)
        self.fc_charr_in = fc_wrap.CharArrayArgWrapper(charr_in)


    def test_extern_decls(self):
        decls1 = '''\
integer(kind=fwrap_npy_intp), intent(in) :: charr1_d1
integer(kind=fwrap_npy_intp), intent(in) :: charr1_d2
character(kind=fwrap_default_character, len=1), dimension(charr1_d1, charr1_d2), intent(inout) :: charr1
'''
        eq_(self.fc_charr1.extern_declarations(), decls1.splitlines())

        decls3 = '''\
integer(kind=fwrap_npy_intp), intent(in) :: charr3_d1
integer(kind=fwrap_npy_intp), intent(in) :: charr3_d2
integer(kind=fwrap_npy_intp), intent(in) :: charr3_d3
integer(kind=fwrap_npy_intp), intent(in) :: charr3_d4
character(kind=fwrap_default_character, len=1), dimension(charr3_d1, charr3_d2, charr3_d3, charr3_d4), intent(inout) :: charr3
'''
        eq_(self.fc_charr3.extern_declarations(), decls3.splitlines())

        decls_star = '''\
integer(kind=fwrap_npy_intp), intent(in) :: cs_d1
integer(kind=fwrap_npy_intp), intent(in) :: cs_d2
character(kind=fwrap_default_character, len=1), dimension(cs_d1, cs_d2), intent(inout) :: cs
'''
        eq_(self.fc_charr_star.extern_declarations(), decls_star.splitlines())

    def test_intern_decls(self):
        eq_(self.fc_charr1.intern_declarations(), 
                ["character(20), dimension(charr1_d2) :: fw_charr1"])
        eq_(self.fc_charr3.intern_declarations(), 
                ["character(30), dimension(charr3_d2, "
                 "charr3_d3, charr3_d4) :: fw_charr3"])
        eq_(self.fc_charr_star.intern_declarations(), 
                # XXX: this should be ... dimension(n1) ...
                ['character(kind=fwrap_char_xX, '
                 'len=cs_d1), dimension(cs_d2) :: fw_cs'])

    def test_extern_arg_list(self):
        eq_(self.fc_charr1.extern_arg_list(), 
                ['charr1_d1', 'charr1_d2', 'charr1'])
        eq_(self.fc_charr3.extern_arg_list(), 
                ['charr3_d1', 'charr3_d2', 
                 'charr3_d3', 'charr3_d4', 'charr3'])
        eq_(self.fc_charr_star.extern_arg_list(),
                ['cs_d1', 'cs_d2', 'cs'])

    def test_pre_call_code(self):
        #XXX: there should be a test in the generated code along the lines of:
        # if(len(ch) .ne. size(fw_ch)) then
        #    ... set error flag and return ...
        #    return
        # endif
        eq_(self.fc_charr1.pre_call_code(),
                ["fw_charr1 = reshape(transfer"
                 "(charr1, fw_charr1), shape(fw_charr1))"])
        eq_(self.fc_charr3.pre_call_code(),
                ["fw_charr3 = reshape(transfer"
                 "(charr3, fw_charr3), shape(fw_charr3))"])
        eq_(self.fc_charr_star.pre_call_code(),
                ["fw_cs = reshape(transfer(cs, fw_cs), shape(fw_cs))"])

    def test_post_call_code(self):
        eq_(self.fc_charr1.post_call_code(),
                ["charr1 = reshape(transfer"
                 "(fw_charr1, charr1), shape(charr1))"])
        eq_(self.fc_charr3.post_call_code(),
                ["charr3 = reshape(transfer"
                 "(fw_charr3, charr3), shape(charr3))"])
        eq_(self.fc_charr_star.post_call_code(),
                ["cs = reshape(transfer(fw_cs, cs), shape(cs))"])
        eq_(self.fc_charr_in.post_call_code(),
                [])
 
class test_array_arg_wrapper(object):

    def setup(self):
        self.real_arr_arg = pyf.Argument('real_arr_arg', 
                                pyf.default_real, 
                                dimension=(':',':',':'), intent='out')
        self.int_arr_arg = pyf.Argument('arr_arg', 
                                pyf.default_integer, 
                                dimension=(':',':'), intent='inout')
        self.int_arr_wrapper = fc_wrap.ArrayArgWrapper(self.int_arr_arg)
        self.real_arr_wrapper = fc_wrap.ArrayArgWrapper(self.real_arr_arg)

        self.real_explicit_arg = pyf.Argument('real_exp_arg', 
                                pyf.default_real, 
                                dimension=('d1', 'd2', 'd3'), intent='inout')

    def test_extern_decls(self):
        int_decls = '''\
integer(kind=fwrap_npy_intp), intent(in) :: arr_arg_d1
integer(kind=fwrap_npy_intp), intent(in) :: arr_arg_d2
integer(kind=fwrap_default_integer), dimension(arr_arg_d1, arr_arg_d2), intent(inout) :: arr_arg
'''
        real_decls = '''\
integer(kind=fwrap_npy_intp), intent(in) :: real_arr_arg_d1
integer(kind=fwrap_npy_intp), intent(in) :: real_arr_arg_d2
integer(kind=fwrap_npy_intp), intent(in) :: real_arr_arg_d3
real(kind=fwrap_default_real), dimension(real_arr_arg_d1, real_arr_arg_d2, real_arr_arg_d3), intent(out) :: real_arr_arg
'''
        eq_(self.int_arr_wrapper.extern_declarations(), 
                int_decls.splitlines())
        eq_(self.real_arr_wrapper.extern_declarations(), 
                real_decls.splitlines())

    def test_extern_arg_list(self):
        eq_(self.int_arr_wrapper.extern_arg_list(), 
                ['arr_arg_d1', 'arr_arg_d2', 'arr_arg'])
        eq_(self.real_arr_wrapper.extern_arg_list(), 
                ['real_arr_arg_d1', 'real_arr_arg_d2', 
                 'real_arr_arg_d3', 'real_arr_arg'])

class test_char_arg(object):

    def setup(self):
        dchar1 = pyf.CharacterType('char_20', len='20', odecl='character*20')
        dchar2 = pyf.CharacterType('char_10', 
                len='10', odecl='character(len=10)')
        dchar3 = pyf.CharacterType('char_x', 
                len='*', odecl='character(len=*)')

        names = ['ch1', 'ch2', 'ch3']

        dchs = [dchar1, dchar2, dchar3]

        inout_args = [pyf.Argument(name=name, dtype=dch, intent='inout') 
                for (name, dch) in zip(names, dchs)]

        self.inout_wraps = [fc_wrap.ArgWrapperFactory(ioa) 
                for ioa in inout_args]

    def test_c_declarations(self):
        results = [
                ['fwrap_npy_intp *fw_ch1_len',
                 'fwrap_default_character *ch1'],
                ['fwrap_npy_intp *fw_ch2_len',
                 'fwrap_default_character *ch2'],
                ['fwrap_npy_intp *fw_ch3_len',
                 'fwrap_default_character *ch3'],
                ]
        for wrap, result in zip(self.inout_wraps, results):
            eq_(wrap.c_declarations(), result)

    def test_extern_decl(self):
        results = [
                ['integer(kind=fwrap_npy_intp), intent(in) :: fw_ch1_len',
                 'character(kind=fwrap_default_character, len=1), '
                     'dimension(fw_ch1_len), intent(inout) :: ch1'],
                
                ['integer(kind=fwrap_npy_intp), intent(in) :: fw_ch2_len',
                 'character(kind=fwrap_default_character, len=1), '
                     'dimension(fw_ch2_len), intent(inout) :: ch2'],

                ['integer(kind=fwrap_npy_intp), intent(in) :: fw_ch3_len',
                 'character(kind=fwrap_default_character, len=1), '
                     'dimension(fw_ch3_len), intent(inout) :: ch3'],
                ]
        for wrap, result in zip(self.inout_wraps, results):
            eq_(wrap.extern_declarations(), result)

    def test_intern_decl(self):
        results = [
                ['character*20 :: fw_ch1'],
                ['character(len=10) :: fw_ch2'],
                ['character(kind=fwrap_char_x, len=fw_ch3_len) :: fw_ch3'],
                ]

        for wrap, result in zip(self.inout_wraps, results):
            eq_(wrap.intern_declarations(), result)

    def test_pre_call_code(self):
        #XXX: there should be a test in the generated code along the lines of:
        # if(len(ch) .ne. size(fw_ch)) then
        #    ... set error flag and return ...
        #    return
        # endif

        results =  ( ['fw_ch1 = transfer(ch1, fw_ch1)'],
                     ['fw_ch2 = transfer(ch2, fw_ch2)'],
                     ['fw_ch3 = transfer(ch3, fw_ch3)'])

        for wrap, result in zip(self.inout_wraps, results):
            eq_(wrap.pre_call_code(), result)

    def test_post_call_code(self):
        #XXX: see comment for test_pre_call_code.
        results =  ( ['ch1 = transfer(fw_ch1, ch1)'],
                     ['ch2 = transfer(fw_ch2, ch2)'],
                     ['ch3 = transfer(fw_ch3, ch3)'])

        for wrap, result in zip(self.inout_wraps, results):
            eq_(wrap.post_call_code(), result)

class test_arg_wrapper(object):

    def setup(self):
        dint = pyf.IntegerType('fwrap_int')
        dlgcl = pyf.default_logical

        self.int_arg = pyf.Argument(name='int', dtype=dint, intent='inout')
        self.int_arg_wrap = fc_wrap.ArgWrapperFactory(self.int_arg)

        self.lgcl_arg = pyf.Argument(name='lgcl', dtype=dlgcl, intent='inout')
        self.lgcl_arg_wrap = fc_wrap.ArgWrapperFactory(self.lgcl_arg)

        self.lgcl_arg_in = pyf.Argument(name='lgcl_in', 
                                dtype=dlgcl, intent='in')
        self.lgcl_arg_in_wrap = fc_wrap.ArgWrapperFactory(self.lgcl_arg_in)

    def test_extern_int_arg(self):
        eq_(self.int_arg_wrap.extern_declarations(), 
                [self.int_arg.declaration()])

    def test_intern_int_var(self):
        eq_(self.int_arg_wrap.intern_declarations(), [])

    def test_pre_call_code_int(self):
        eq_(self.int_arg_wrap.pre_call_code(), [])

    def test_post_call_code_int(self):
        eq_(self.int_arg_wrap.post_call_code(), [])

    def test_extern_lgcl_arg(self):
        eq_(self.lgcl_arg_wrap.extern_declarations(),
                ['integer(kind=fwrap_default_logical), '
                    'intent(inout) :: lgcl'])
        eq_(self.lgcl_arg_in_wrap.extern_declarations(),
                ['integer(kind=fwrap_default_logical), '
                    'intent(in) :: lgcl_in'])

    def test_intern_lgcl_var(self):
        eq_(self.lgcl_arg_wrap.intern_declarations(), [])
        eq_(self.lgcl_arg_in_wrap.intern_declarations(), [])

    def test_post_call_code(self):
        for argw in (self.lgcl_arg_wrap, self.lgcl_arg_in_wrap):
            eq_(argw.post_call_code(), [])

class test_arg_wrapper_manager(object):
    
    def setup(self):
        dlgcl = pyf.default_logical
        dint = pyf.IntegerType(fw_ktp='int')
        self.lgcl1 = pyf.Argument(name='lgcl1', dtype=dlgcl, intent='inout')
        self.lgcl2 = pyf.Argument(name='lgcl2', dtype=dlgcl, intent='inout')
        self.intarg = pyf.Argument(name='int', dtype=dint, intent='inout')
        self.args = [self.lgcl1, self.lgcl2, self.intarg]
        self.l1wrap = fc_wrap.ArgWrapper(self.lgcl1)
        self.l2wrap = fc_wrap.ArgWrapper(self.lgcl2)
        self.am = fc_wrap.ArgWrapperManager(self.args, isfunction=False)

    def test_arg_declarations(self):
        decls = '''\
integer(kind=fwrap_default_logical), intent(inout) :: lgcl1
integer(kind=fwrap_default_logical), intent(inout) :: lgcl2
integer(kind=fwrap_int), intent(inout) :: int
'''.splitlines()
        eq_(self.am.arg_declarations(), decls)

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

class test_arg_manager_return(object):

    def setup(self):
        dlgcl = pyf.default_logical
        dint = pyf.IntegerType(fw_ktp='int')
        self.lgcl = pyf.Argument(name='ll', dtype=dlgcl, 
                intent='out', is_return_arg=True)
        self.int = pyf.Argument(name='int', dtype=dint, 
                intent='out', is_return_arg=True)
        self.am_lgcl = fc_wrap.ArgWrapperManager([self.lgcl], isfunction=True)
        self.am_int = fc_wrap.ArgWrapperManager([self.int], isfunction=True)

    def test_declarations(self):
        declaration = '''\
integer(kind=fwrap_default_logical) :: ll
'''.splitlines()
        eq_(self.am_lgcl.arg_declarations(), declaration)

    def test_temp_declarations(self):
        eq_(self.am_lgcl.temp_declarations(), [])

class test_c_proto_generation(object):
    
    def test_c_proto_args(self):
        args = [pyf.Argument(name='int_arg', 
                        dtype=pyf.default_integer, intent='in'),
                pyf.Argument(name='real_arg', 
                        dtype=pyf.default_real,    intent='out')]
        return_arg = pyf.Argument(name='fname', dtype=pyf.default_real)
        arg_man = fc_wrap.ArgWrapperManager([return_arg]+args, 
                                isfunction=True)
        eq_(arg_man.c_proto_args(), 
                ['fwrap_default_real *fname', 
                 'fwrap_default_integer *int_arg', 
                 'fwrap_default_real *real_arg'])

    def test_c_proto_array_args(self):
        args = [pyf.Argument(name='array', 
                        dtype=pyf.default_real, 
                        dimension=(':',)*3, intent='out')]
        arg_man = fc_wrap.ArgWrapperManager(args, isfunction=False)
        eq_(arg_man.c_proto_args(), ['fwrap_npy_intp *array_d1',
                                     'fwrap_npy_intp *array_d2',
                                     'fwrap_npy_intp *array_d3',
                                     'fwrap_default_real *array'])

    def test_c_proto_return_type(self):
        for dtype in (pyf.default_real, pyf.default_integer):
            return_arg = pyf.Argument(name='ret_arg', 
                                dtype=dtype, is_return_arg=True)
            am = fc_wrap.ArgWrapperManager([return_arg], isfunction=True)
            eq_(am.c_proto_return_type(), 'void')

        am_subr = fc_wrap.ArgWrapperManager([], isfunction=False)
        eq_(am_subr.c_proto_return_type(), 'void')

    def test_c_prototype_empty(self):
        return_arg = pyf.Argument(name="empty_func", 
                            dtype=pyf.default_integer)
        empty_func = pyf.Function(name='empty_func',
                          args=(),
                          return_arg=return_arg)
        empty_func_wrapper = fc_wrap.FunctionWrapper(wrapped=empty_func)
        eq_(empty_func_wrapper.c_prototype(), 
                ('void empty_func_c(fwrap_default_integer *fw_ret_arg, '
                    'fwrap_default_integer *fw_iserr__);'))
        empty_subr = pyf.Subroutine(name='empty_subr',
                            args=())
        empty_subr_wrapper = fc_wrap.SubroutineWrapper(wrapped=empty_subr)
        eq_(empty_subr_wrapper.c_prototype(), 
                'void empty_subr_c(fwrap_default_integer *fw_iserr__);')

    def test_c_prototype_args(self):
        args = [pyf.Argument(name='int_arg', 
                        dtype=pyf.default_integer, intent='in'),
                pyf.Argument(name='array', 
                        dtype=pyf.default_real, 
                        dimension=(':',)*3, intent='out')]
        return_arg = pyf.Argument(name="func", dtype=pyf.default_integer)
        func = pyf.Function(name='func', args=args, return_arg=return_arg)
        func_wrapper = fc_wrap.FunctionWrapper(wrapped=func)
        eq_(func_wrapper.c_prototype(), "void func_c"
                                        "(fwrap_default_integer *fw_ret_arg, "
                                        "fwrap_default_integer *int_arg, "
                                        "fwrap_npy_intp *array_d1, "
                                        "fwrap_npy_intp *array_d2, "
                                        "fwrap_npy_intp *array_d3, "
                                        "fwrap_default_real *array, "
                                        "fwrap_default_integer *fw_iserr__);")

# many_arrays_text#{{{
many_arrays_text = '''\
subroutine arr_args_c(assumed_size_d1, assumed_size_d2, assumed_size, d1, assumed_shape_d1, assumed_shape_d2, assumed_shape, explicit_shape_d1, explicit_shape_d2, explicit_shape, c1, c2, fw_iserr__) bind(c, name="arr_args_c")
    use fwrap_ktp_mod
    implicit none
    integer(kind=fwrap_npy_intp), intent(in) :: assumed_size_d1
    integer(kind=fwrap_npy_intp), intent(in) :: assumed_size_d2
    integer(kind=fwrap_default_integer), dimension(assumed_size_d1, assumed_size_d2), intent(inout) :: assumed_size
    integer(kind=fwrap_default_integer), intent(in) :: d1
    integer(kind=fwrap_npy_intp), intent(in) :: assumed_shape_d1
    integer(kind=fwrap_npy_intp), intent(in) :: assumed_shape_d2
    integer(kind=fwrap_default_logical), dimension(assumed_shape_d1, assumed_shape_d2), intent(out) :: assumed_shape
    integer(kind=fwrap_npy_intp), intent(in) :: explicit_shape_d1
    integer(kind=fwrap_npy_intp), intent(in) :: explicit_shape_d2
    complex(kind=fwrap_default_complex), dimension(explicit_shape_d1, explicit_shape_d2), intent(inout) :: explicit_shape
    integer(kind=fwrap_default_integer), intent(inout) :: c1
    integer(kind=fwrap_default_integer) :: c2
    integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
    interface
        subroutine arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
            use fwrap_ktp_mod
            implicit none
            integer(kind=fwrap_default_integer), intent(in) :: d1
            integer(kind=fwrap_default_logical), dimension(:, :), intent(out) :: assumed_shape
            integer(kind=fwrap_default_integer), intent(inout) :: c1
            integer(kind=fwrap_default_integer) :: c2
            integer(kind=fwrap_default_integer), dimension(d1, *), intent(inout) :: assumed_size
            complex(kind=fwrap_default_complex), dimension(c1, c2), intent(inout) :: explicit_shape
        end subroutine arr_args
    end interface
    fw_iserr__ = FW_INIT_ERR__
    call arr_args(assumed_size, d1, assumed_shape, explicit_shape, c1, c2)
    fw_iserr__ = FW_NO_ERR__
end subroutine arr_args_c
'''
#}}}
