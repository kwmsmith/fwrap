from pyf_support_fwrap import *

#
# Check that the 4 arguments (see pyf_support.f)
# are turned into 2
#


__doc__ = u"""
    >>> m, n = 2, 4
    >>> testone(m, n)
    array([[  0.,   1.,   2.,   3.],
           [  4.,   5.,   6.,   7.],
           [  8.,   9.,  10.,  11.]])

"""
