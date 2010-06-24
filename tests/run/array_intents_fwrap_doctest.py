import numpy as np
from array_intents_fwrap import *

N = 2
arrs = [np.ones((N,N), dtype=np.float32, order='F') for x in range(4)]

__doc__ = u'''
>>> a,b,c = assumed_shape_intents(*arrs)
>>> np.all(a == np.array([[ 1.,  1.],
...               [ 1.,  1.]], dtype=np.float32))
True
>>> np.all(b == np.array([[ 32.,  32.],
...               [ 32.,  32.]], dtype=np.float32)) 
True
>>> np.all(c == np.array([[ 0.25,  0.25],
...               [ 0.25,  0.25]], dtype=np.float32))
True
'''
