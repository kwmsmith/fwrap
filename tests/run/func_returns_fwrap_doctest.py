from func_returns_fwrap import *

def test_rets():
    u'''
    >>> test_rets()
    True
    '''
    return ((1,) == lgcl_ret() and ('k',) == char_ret())
