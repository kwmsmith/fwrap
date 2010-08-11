from ndims_fwrap import *
import numpy as np

N = 5

def test_D1():
    '''
    >>> test_D1()
    True
    '''
    a = np.zeros((N,), dtype=np.bool_)
    acpy = a.copy()
    acpy[...] = True
    acpy[::2] = False
    ar = d1(a)
    return np.all(ar.astype(bool) == acpy)

def test_D2():
    '''
    >>> test_D2()
    True
    '''
    a = np.zeros((N,N), dtype=np.bool_)
    acpy = a.copy()
    acpy[...] = True
    acpy[::2, ::2] = False
    ar = d2(a)
    return np.all(ar.astype(bool) == acpy)

def test_D3():
    '''
    >>> test_D3()
    True
    '''
    a = np.zeros((N,N,N), dtype=np.bool_)
    acpy = a.copy()
    acpy[...] = True
    acpy[::2,:,:] = False
    ar = d3(a)
    return np.all(ar.astype(bool) == acpy.astype(bool))
