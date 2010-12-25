#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import fwrapper
from fwrap import pyf_iface as pyf
from fwrap import configuration

from nose.tools import ok_, eq_, set_trace

def test_cb_subr():

    fsrc = '''\
subroutine caller(cb_, a, b)
    implicit none
    integer a
    real*8 b
    external cb_

    call cb_(a, b)

end subroutine caller
'''

    cfg = configuration.Configuration('empty.pyx')
    ast = fwrapper.parse([fsrc], cfg)
    cb_arg = ast[0].args[0]
    eq_(cb_arg.name, 'cb_')
    eq_(type(cb_arg.dtype), pyf.CallbackType)
    cb_dtype = cb_arg.dtype
    ok_(isinstance(cb_dtype.arg_dtypes[0], pyf.IntegerType))
    ok_(isinstance(cb_dtype.arg_dtypes[1], pyf.RealType))

def test_cb_subr_implicit():

    fsrc = '''\
subroutine caller(cb_, a, b)
    external cb_

    call cb_(a, b)

end subroutine caller
'''

    cfg = configuration.Configuration('empty.pyx')
    ast = fwrapper.parse([fsrc], cfg)
    cb_arg = ast[0].args[0]
    eq_(cb_arg.name, 'cb_')
    eq_(type(cb_arg.dtype), pyf.CallbackType)
    cb_dtype = cb_arg.dtype
    ok_(isinstance(cb_dtype.arg_dtypes[0], pyf.RealType))
    ok_(isinstance(cb_dtype.arg_dtypes[1], pyf.RealType))

def test_cb_func_implicit():
    fsrc = '''\
subroutine caller(cb_, a, b)
    external cb_
    dummy = cb_(a, b)
end subroutine caller
'''

    cfg = configuration.Configuration('empty.pyx')
    ast = fwrapper.parse([fsrc], cfg)
    cb_arg = ast[0].args[0]
    eq_(cb_arg.name, 'cb_')
    eq_(type(cb_arg.dtype), pyf.CallbackType)
    cb_dtype = cb_arg.dtype
    ok_(isinstance(cb_dtype.arg_dtypes[0], pyf.RealType))
    ok_(isinstance(cb_dtype.arg_dtypes[1], pyf.RealType))

def test_cb_func():
    fsrc = '''\
subroutine caller(cb_, a, b)
    implicit none
    integer a
    real*8 b, cb_, dummy
    external cb_
    dummy = cb_(a, b)
end subroutine caller
'''

    cfg = configuration.Configuration('empty.pyx')
    ast = fwrapper.parse([fsrc], cfg)
    cb_arg = ast[0].args[0]
    eq_(cb_arg.name, 'cb_')
    eq_(type(cb_arg.dtype), pyf.CallbackType)
    cb_dtype = cb_arg.dtype
    ok_(isinstance(cb_dtype.arg_dtypes[0], pyf.IntegerType))
    ok_(isinstance(cb_dtype.arg_dtypes[1], pyf.RealType))

def test_cb_arg_expr():
    fsrc = '''
subroutine caller(cb_, a, b)
    implicit none
    integer a
    real*8 b, cb_, dummy
    complex*8 cpx
    external cb_
    cpx = cmplx(1.0,2.0)
    dummy = cb_(a+b, b-cpx)
end subroutine caller
'''
    cfg = configuration.Configuration('empty.pyx')
    ast = fwrapper.parse([fsrc], cfg)
    cb_arg = ast[0].args[0]
    eq_(cb_arg.name, 'cb_')
    eq_(type(cb_arg.dtype), pyf.CallbackType)
    cb_dtype = cb_arg.dtype
    ok_(isinstance(cb_dtype.arg_dtypes[0], pyf.RealType))
    ok_(isinstance(cb_dtype.arg_dtypes[1], pyf.ComplexType))
