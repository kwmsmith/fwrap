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

def test_param_expr():
    u'''
    >>> test_param_expr()
    True
    '''
    # integer, parameter :: d1=1, d2=d1+2+int(3.0), d3=d1+d2
    # integer, dimension(d1:d2+d3, d2:d3+1, -d3:0) :: a
    d1 = 1; d2 = d1+2+3; d3 = d1 + d2
    dim1 = (d2+d3)-(d1)+1
    dim2 = (d3+1)-(d2)+1
    dim3 = (0)-(-d3)+1

    arr = np.empty((dim1, dim2, dim3), dtype=np.int32, order='F')
    compare = arr.copy('F')

    for i_ in range(dim1):
        i = d1 + i_
        for j_ in range(dim2):
            j = d2 + j_
            for k_ in range(dim3):
                k = -d3 + k_
                compare[i_,j_,k_] = i + j + k

    res, = param_expr(arr)

    return np.all(res == compare)


def test_assumed_size():
    u'''
    >>> test_assumed_size()
    True
    '''
    dim = 20-10+1
    arr = np.empty((dim,), dtype=fwi_integer, order='F')

    assumed_size(arr)

    return np.all(arr == 5)
