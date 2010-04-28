from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

from tutils import compare

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
    fc = '''\
    function empty_func_c() bind(c, name="empty_func_c")
        use fwrap_ktp_mod
        implicit none
        integer(fwrap_default_integer) :: empty_func_c
        interface
            function empty_func()
                use fwrap_ktp_mod
                implicit none
                integer(fwrap_default_integer) :: empty_func
            end function empty_func
        end interface
        empty_func_c = empty_func()
    end function empty_func_c
    '''
    compare(fc, buf.getvalue())

def test_generate_h_fc():
    ast = main.generate_ast(fsrc)
    buf = CodeBuffer()
    fc_wrap = main.wrap_fc(ast)
    main.generate_c_header(fc_wrap, buf)
    header = '''\
    #include "fwrap_ktp_header.h"

    fwrap_default_integer empty_func_c();
    '''
    compare(buf.getvalue(), header)

def test_generate_pxd_fc():
    ast = main.generate_ast(fsrc)
    buf = CodeBuffer()
    fc_wrap = main.wrap_fc(ast)
    cy_wrap = main.wrap_cy(fc_wrap)
    main.generate_pxd_fc(cy_wrap, projname="DP", buf=buf)
    header = '''\
    from fwrap_ktp cimport *

    cdef extern from "DP_fc.h":
        fwrap_default_integer empty_func_c()
    '''
    compare(header, buf.getvalue())

def test_generate_pxd_fwrap():
    pass

def test_generate_pyx_fwrap():
    pass
