from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

empty_func = '''
function empty_func()
    implicit none
    integer :: empty_func
end function empty_func
'''

fsrc = StringIO(empty_func)

def test_generate_ast():
    ast = main.generate_ast(fsrc)
    empty_func = pyf.Function(name='empty_func',
                    args=(),
                    return_type=pyf.default_integer)
    eq_(ast[0].name, empty_func.name)
    eq_(ast[0].return_arg.name, empty_func.return_arg.name)
    eq_(ast[0]._args, empty_func._args)

def test_generate_fc():
    ast = main.generate_ast(fsrc)
    buf = CodeBuffer()
    fc_wrap = main.wrap_fc(ast)
    main.generate_fc(fc_wrap, buf)

def test_generate_c_header():
    ast = main.generate_ast(fsrc)
    buf = CodeBuffer()
    fc_wrap = main.wrap_fc(ast)
    main.generate_c_header(fc_wrap, buf)
