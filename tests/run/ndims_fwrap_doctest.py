from ndims_fwrap import *
import numpy as np

N = 5

def test_D1():
    # '''
    # >>> test_D1()
    # '''
    a = np.zeros((N,), dtype=np.bool_)
    ar, = d1(a)
    print ar

def test_D2():
    # '''
    # >>> test_D2()
    # '''
    a = np.zeros((N,N), dtype=np.bool_)
    ar, = d2(a)
    print ar

def test_D3():
    '''
    >>> test_D3()
    True
    '''
    a = np.zeros((N,N,N), dtype=np.bool_)
    acpy = a.copy()
    acpy[...] = True
    acpy[::2,:,:] = False
    ar, = d3(a)
    print np.all(ar == acpy)
    # print "acpy", acpy
    # print "ar", ar
