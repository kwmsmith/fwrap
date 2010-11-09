from pyf_support_fwrap import *

#
# Check that explicit-shape intent(out) arrays can be
# created automatically
#


__doc__ = u"""
    >>> m, n = 2, 4
    >>> testone(m, n)
    array([[  0.,   1.,   2.,   3.],
           [  4.,   5.,   6.,   7.],
           [  8.,   9.,  10.,  11.]])

"""
