from cmplx_array_fwrap import *
import numpy as np

carr = np.empty((2,2), dtype=np.complex128, order='F')

__doc__ = u'''\
>>> np.all(complex_array(carr) == np.array([[ 1.+2.j,  1.+2.j], [ 1.+2.j,  1.+2.j]]))
True
'''
