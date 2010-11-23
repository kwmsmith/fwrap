from templates_fwrap import *
import numpy as np

#
# The testcase is very simple and not very exciting;
# the point is what Cython code is generated with
# the --detect-templates switch.
#

__doc__ = u"""
    >>> sfoo(5, np.arange(5).astype(np.float32))
    array([ 0.,  1.,  2.,  3.,  4.], dtype=float32)
    >>> dfoo(5, np.arange(5).astype(np.float64))
    array([ 0.,  2.,  4.,  6.,  8.])
    >>> cfoo(5, np.arange(5).astype(np.complex64))
    array([  0.+0.j,   3.+0.j,   6.+0.j,   9.+0.j,  12.+0.j], dtype=complex64)
    >>> zfoo(5, np.arange(5).astype(np.complex128))
    array([  0.+0.j,   4.+0.j,   8.+0.j,  12.+0.j,  16.+0.j])

    >>> other(5, np.arange(5))
    array([ 0.,  1.,  2.,  3.,  4.])
    >>> gfoo(5, np.arange(5))
    array([ 0.,  1.,  2.,  3.,  4.])

"""
