#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import pyf_iface as pyf
from nose.tools import ok_, eq_, set_trace, assert_raises, raises

class test_dtype_selector(object):

    def test_create(self):
        real_star = pyf.RealType("real_star", length="8")
        eq_(real_star.odecl, "real*8")

class test_program_units(object):
    def test_function(self):
        return_arg = pyf.Argument('fort_function', dtype=pyf.default_integer)
        ffun = pyf.Function(name="fort_function",
                args=(),
                return_arg=return_arg)
        ok_(ffun.name == 'fort_function')
        ok_(ffun.return_arg.dtype is pyf.default_integer)

    def test_function_args(self):
        name = 'ffun'
        return_arg = pyf.Argument(name, dtype=pyf.default_integer)
        pyf.Function(name=name,
                args=(pyf.Argument('a', dtype=pyf.default_integer),),
                return_arg=return_arg)

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

def test_func_return_array():
    args = [pyf.Argument(name='a', dtype=pyf.default_integer, intent='in'),
            pyf.Argument(name='b', dtype=pyf.default_integer, intent='in')]
    return_arg = pyf.Argument(name="arr_fun",
                              dtype=pyf.default_real,
                              dimension=('a', 'b'))
    arrfun = pyf.Function(name="arr_fun",
                            args=args,
                            return_arg=return_arg)







def test_valid_proc_name():
    ok_(pyf.Procedure('name', ()))
    assert_raises(pyf.InvalidNameException, pyf.Procedure, '_a', ())

def test_valid_arg_name():
    ok_(pyf.Argument('name', pyf.default_integer))
    assert_raises(pyf.InvalidNameException,
                        pyf.Argument, '_a', pyf.default_integer)

class test_arg_manager(object):

    def test_declaration_order(self):
        array_arg = pyf.Argument('arr',
                pyf.default_integer, 'in', dimension=('d1', 'd2'))
        d1 = pyf.Argument('d1', pyf.default_integer, 'in')
        d2 = pyf.Argument('d2', pyf.default_integer, 'in')
        am = pyf.ArgManager([array_arg, d2, d1])
        decls = '''\
integer(kind=fwi_integer_t), intent(in) :: d2
integer(kind=fwi_integer_t), intent(in) :: d1
integer(kind=fwi_integer_t), dimension(d1, d2), intent(in) :: arr
'''
        eq_(am.arg_declarations(), decls.splitlines())

def test_parameter():
    param = pyf.Parameter(name='FOO',
                dtype=pyf.default_integer, expr='kind(1.0D0)')
    arg = pyf.Argument(name="fooarg",
                dtype=pyf.RealType("foo_real", kind="FOO"),
                intent="inout")
    subr = pyf.Subroutine(name="foosubr",
                          args=[arg],
                          params=[param])

def test_dtype():
    assert_raises(pyf.InvalidNameException,
                        pyf.IntegerType, 'selected_int_kind(10)')
    assert_raises(pyf.InvalidNameException,
                        pyf.RealType, 'selected_real_kind(10)')

def test_valid_fort_name():
    ok_(pyf.valid_fort_name('F12_bar'))
    ok_(pyf.valid_fort_name('a'*63))
    ok_(not pyf.valid_fort_name('a'*64))
    ok_(not pyf.valid_fort_name('_a'))
    ok_(not pyf.valid_fort_name('1a'))
    ok_(not pyf.valid_fort_name(' a'))
