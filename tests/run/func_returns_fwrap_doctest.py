from func_returns_fwrap import *

def test_rets():
    u'''
    >>> test_rets()
    (True, 'k')
    '''
    return (bool(lgcl_ret()), char_ret())
