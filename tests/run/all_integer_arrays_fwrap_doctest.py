from all_integer_arrays_fwrap import *
import numpy as np

n1, n2 = 3, 4
ain = np.empty((n1,n2), dtype=np.int32, order='F')
aout = ain.copy('F')
ainout = ain.copy('F')
ano = ain.copy('F')

aout_, ainout_, ano_ = (np.array([[ 2,  2,  2,  2], [ 2,  2,  2,  2], [
                            2,  2,  2,  2]], dtype=np.int32),
                        np.array([[ 36,  36,  36,  36], [ 36,  36,  36,
                            36], [ 36,  36,  36,  36]], dtype=np.int32),
                        np.array([[ 34,  34,  34,  34], [ 34,  34,  34,
                            34], [ 34,  34, 34,  34]], dtype=np.int32))

def init(ain, aout, ainout, ano):
    ain.fill(2)
    aout.fill(0)
    ainout.fill(34)
    ano.fill(0)

def test_results(func, args, results):
    res_ = func(*args)
    for r1, r2 in zip(res_, results):
        if not np.all(r1 == r2):
            print r1
            print r2
            return False
    return True

__doc__ = u'''
>>> init(ain, aout, ainout, ano)
>>> test_results(assumed_shape, (ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
>>> init(ain, aout, ainout, ano)
>>> test_results(explicit_shape, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
>>> init(ain, aout, ainout, ano)
>>> test_results(assumed_size, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
'''
