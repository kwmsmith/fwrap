from fwrap_src import cy_wrap
from fwrap_src import pyf_iface as pyf
from cStringIO import StringIO

def test_empty_func():
    empty_func = pyf.function(name='empty_func',
                        args=(),
                        return_type=pyf.default_integer)
    buf = StringIO()
    cy_wrap.generate([empty_func], buf)
    cy_wrapper = '''
#XXX cpdef int empty_func():
'''

