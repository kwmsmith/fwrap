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
