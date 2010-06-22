from all_logicals_fwrap import *

__doc__ = u'''
>>> log_default(1,0) == (0, 0)
True
>>> print log_x_len(1,2,4,5,7,8,10,11) == (0, 0, 0, 0, 0, 0, 0L, 0L)
True
>>> print log_kind_x(1,2,4,5,7,8,10,11) == (0, 0, 0, 0, 0, 0, 0L, 0L)
True
'''
