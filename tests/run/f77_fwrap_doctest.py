from f77_fwrap import *
import numpy as np

n1, n2 = 3, 4
ain = np.empty((n1,n2), dtype=np.float32, order='F')
aout = ain.copy('F')
ainout = ain.copy('F')
ano = ain.copy('F')

aout_ = aout.copy('F')
ainout_ = ainout.copy('F')
ano_ = ano.copy('F')

def init():
    ain.fill(2.0)
    aout.fill(0.0)
    ainout.fill(34.0)
    ano.fill(0.0)

    aout_[...] = ain
    ano_[...] = ainout
    ainout_[...] = ain + ano_


def test_results(func, args, results):
    res_ = func(*args)
    for r1, r2 in zip(res_, results):
        if not np.all(r1 == r2):
            print r1
            print r2
            return False
    return True

__doc__ = u'''
    >>> int_default(1,2) == (6, 2)
    True
    >>> int_x_len(1,2,4,5,7,8,10,11) == (2, 3, 5, 9, 8, 15, 11L, 21L)
    True
    >>> int_kind_x(1,2,4,5,7,8,10,11) == (2, 3, 5, 9, 8, 15, 11L, 21L)
    True


    >>> init()
    >>> test_results(explicit_shape, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
    True
    >>> init()
    >>> test_results(assumed_size, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
    True

    >>> double_if_a('B', 8), double_if_a('A', 8)  # TODO Python 3
    (8, 16)
    
    >>> emit_f() # TODO Python 3
    'F'
'''
