from fwrap_src import pyf_iface as pyf

from nose.tools import ok_, eq_, set_trace

class test_program_units(object):
    def test_function(self):
        ffun = pyf.Function(name="fort_function",
                args=(),
                return_type=pyf.default_integer)
        ok_(ffun.args == ())
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
