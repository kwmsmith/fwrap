from kind_params_fwrap import *

def test_kind_params():
    '''
    >>> test_kind_params()
    True
    '''
    return kind_params(5, 5, 5) == (16, 17.0, 18.0)
