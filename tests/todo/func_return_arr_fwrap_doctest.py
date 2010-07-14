from func_return_arr_fwrap import *
import numpy as np

a, b = 3, 5
outarr = np.empty((a,b), dtype=np.int32, order='F')
outarr.fill(-20)

__doc__ = u'''
>>> ret_arr(a, b)
'''
