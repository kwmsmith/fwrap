from all_complex_fwrap import *

__doc__ = u'''
>>> complex_default(1+1j,2+2j) == ((2+2j), (-1-1j))
True
>>> complex_x_len(10+10j,11+11j,13+13j,14+14j) == ((20+20j), (10+10j), (13-13j), -26j)
True
>>> complex_kind_x(7+7j,8+8j,10+10j,11+11j) == ((7+7j), 49j, (-2000+2000j), (-2010+2010j))
True
'''
