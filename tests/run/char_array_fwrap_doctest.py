from char_array_fwrap import *
import numpy as np

charr = np.empty((2,3), dtype='|S3', order='F')
charr1 = np.empty((2,3), dtype='|S1', order='F')

__doc__ = u'''\
>>> np.all(char_array(charr) == np.array([['abc', 'abc', 'abc'], ['abc', 'abc', 'abc']], dtype='|S3'))
True
>>> np.all(char1_arr(charr1) == np.array([['%', '%', '%'], ['%', '%', '%']], dtype='|S1'))
True
>>> np.all(char_star(charr) == np.array([['123', '123', '123'], ['123', '123', '123']], dtype='|S3'))
True
'''

# FIXME:
# Yields a bus error -- passing an 'S3' when Fortran expects a character(len=1)
# dtype.
# Requires a runtime check to make sure the 'itemsize' of the dtype string
# passed in == the 'len' of the fortran character dtype.
# >>> np.all(char1_arr(charr) == np.array([['%', '%', '%'], ['%', '%', '%']], dtype='|S1'))
