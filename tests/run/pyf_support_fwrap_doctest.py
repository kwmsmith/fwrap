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
    >>> testone(m)
    array([[ 0.,  1.],
           [ 2.,  3.],
           [ 4.,  5.]])

    >>> testone(10, n) # m_hidden == m+1
    Traceback (most recent call last):
        ...
    ValueError: Condition on arguments not satisfied: (m >= 1) and (m_hidden <= 10)

    >>> reorders(1, 3, np.arange(4).astype(np.int32))
    (3, 1, array([2, 2, 2, 2], dtype=int32))

    >>> r = np.arange(10)
    >>> fort_sum_simple(r, 10)
    45.0
    >>> fort_sum_simple(r)
    45.0

    
#    >>> fort_sum_simpl(7, r, 3)
#    45.0
"""
