from fwrap_src import pyf_iface as pyf

from nose.tools import ok_, eq_, set_trace

class test_program_units(object):
    def test_function(self):
        ffun = pyf.function(name="fort_function",
                args=(),
                return_type=pyf.default_integer)
        ok_(ffun.args == ())
        ok_(ffun.name == 'fort_function')
        ok_(ffun.return_type is pyf.default_integer)

    def test_function_args(self):
        pyf.function(name="ffun",
                args=('a', 'b', 'c'),
                return_type=pyf.default_integer)

    def test_subroutine(self):
        pyf.subroutine(name='subr',
                args=())

    def test_module(self):
        pyf.module(name='mod')

    def test_module_use(self):
        mod1 = pyf.module(
                name='mod1',
                mod_objects=[
                    pyf.var(name='i', dtype=pyf.default_integer),
                    pyf.var(name='r', dtype=pyf.default_real),
                    pyf.var(name='c', dtype=pyf.default_complex),
                    ]
                )

        pyf.module(
                name='mod',
                uses=[
                    pyf.use(mod1, only=('i', 'r')),
                    ]
                )
