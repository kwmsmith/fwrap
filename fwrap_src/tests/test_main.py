from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf

from nose.tools import ok_, eq_, set_trace

def test_generate_ast():
    fsrc = StringIO('''
function empty_func()
    implicit none
    integer :: empty_func
end function empty_func
''')
    ast = main.generate_ast()
    empty_func = pyf.Function(name='empty_func',
                    args=(),
                    return_type=pyf.default_integer)
    eq_(ast, [empty_func])
