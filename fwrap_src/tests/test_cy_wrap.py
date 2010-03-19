from fwrap_src import cy_wrap
from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from cStringIO import StringIO

from nose.tools import ok_, eq_, set_trace

class test_empty_func(object):

    def setup(self):
        self.empty_func = pyf.Function(name='empty_func',
                            args=(),
                            return_type=pyf.default_integer)
        self.buf = StringIO()

    def test_empty_func_pyx_wrapper(self):
        cy_wrap.generate_pyx([self.empty_func], self.buf)
        pyx_wrapper = '''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func():
    return DP_c.empty_func_c()
'''.splitlines()
        eq_(pyx_wrapper, self.buf.getvalue().splitlines())
    

    def test_empty_func_pxd_wrapper(self):
        cy_wrap.generate_pxd([self.empty_func], self.buf)
        pxd_wrapper = '''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func()
'''.splitlines()
        eq_(pxd_wrapper, self.buf.getvalue().splitlines())


class test_cy_arg_wrapper(object):

    def setup(self):
        self.dts = ('default_integer', 'default_real')
        self.caws = []
        for dt in self.dts:
            fc_arg = fc_wrap.ArgWrapper(pyf.Argument('foo', dtype=getattr(pyf, dt), intent='in'))
            self.caws.append(cy_wrap.CyArgWrapper(fc_arg))

    def test_extern_declarations(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.extern_declarations(), ["fwrap_%s foo" % dt])

    def test_intern_declarations(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.intern_declarations(), [])

    def test_intern_name(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.intern_name(), "foo")

class test_cy_arg_wrapper_mgr(object):

    def setup(self):
        self.dts = ("default_integer", "default_real")
        self.cy_args = []
        for dt in self.dts:
            fwarg = fc_wrap.ArgWrapper(pyf.Argument('foo_%s' % dt, dtype=getattr(pyf, dt), intent='in'))
            self.cy_args.append(cy_wrap.CyArgWrapper(fwarg))
        self.rtn = "fwrap_default_integer"
        self.mgr = cy_wrap.CyArgWrapperManager(args=self.cy_args, return_type_name=self.rtn)

    def test_arg_declarations(self):
        eq_(self.mgr.arg_declarations(), [cy_arg.extern_declarations()[0] for cy_arg in self.cy_args])

    def test_call_arg_list(self):
        eq_(self.mgr.call_arg_list(), ["&%s" % cy_arg.intern_name() for cy_arg in self.cy_args])

    def test_return_arg_declaration(self):
        eq_(self.mgr.return_arg_declaration(), ["%s fwrap_return" % self.rtn])

class test_cy_proc_wrapper(object):

    def setup(self):
        pyf_func = pyf.Function(name="fort_func",
                args=[ pyf.Argument(name="int_arg", dtype=pyf.default_integer, intent='in'),
                       pyf.Argument(name="real_arg", dtype=pyf.default_real, intent='in'),
                     ],
                return_type=pyf.default_integer
                )
        func_wrapper = fc_wrap.FunctionWrapper(name="fort_func_c", wrapped=pyf_func)
        self.cy_func_wrapper = cy_wrap.ProcWrapper(name="fort_func", wrapped=func_wrapper)

        pyf_subr = pyf.Subroutine(name="fort_subr",
                args=[ pyf.Argument(name="real_arg", dtype=pyf.default_real, intent='in'),
                       pyf.Argument(name="int_arg", dtype=pyf.default_integer, intent='in'),
                     ]
                )
        subr_wrapper = fc_wrap.SubroutineWrapper(name="fort_subr_c", wrapped=pyf_subr)
        self.cy_subr_wrapper = cy_wrap.ProcWrapper(name="fort_subr", wrapped=subr_wrapper)

    def test_cy_proc_wrapper_fort_func(self):
        eq_(self.cy_func_wrapper.procedure_decl(), "cpdef fwrap_default_integer fort_func(fwrap_default_integer int_arg, fwrap_default_real real_arg):")

    def test_cy_proc_wrapper_fort_subr(self):
        eq_(self.cy_subr_wrapper.procedure_decl(), "cpdef object fort_subr(fwrap_default_real real_arg, fwrap_default_integer int_arg):")
