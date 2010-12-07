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
    # set_trace()
