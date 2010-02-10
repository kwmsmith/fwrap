from fwrap_src import cy_wrap
from fwrap_src import pyf_iface as pyf
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
