from dim_expr_fwrap import *
import numpy as np
from numpy import array

def test_const_expr(bad_size=False):
    u'''
    >>> test_const_expr()
    True

    >>> test_const_expr(bad_size=True) # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    RuntimeError: ...
    '''
    lbound, ubound = 10, 20
    extent = ubound-lbound+1
    if bad_size:
        extent -= 2
    arr = np.empty(extent, dtype=np.int32, order='F')
    arr.fill(0)

    (arr,) = const_expr(arr)
    return np.all(arr == array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]))

def test_arg_expr(bad_size=False):
    u"""
    >>> test_arg_expr()
    True

    >>> test_arg_expr(bad_size=True) # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    RuntimeError: ...
    """
    n1, n2 = 2, 3
    extent = (n1+n2*2) - (n1-n1+3) + 1
    if bad_size:
        extent -= 1
    arr = np.empty(extent, dtype=np.int32, order='F')
    res, = arg_expr(arr, n1, n2)
    return np.all(res == 12)
