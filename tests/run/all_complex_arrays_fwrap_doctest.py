from all_complex_arrays_fwrap import *
import numpy as np

n1, n2 = 3, 4
ain = np.empty((n1,n2), dtype=np.complex64, order='F')
aout = ain.copy('F')
ainout = ain.copy('F')
ano = ain.copy('F')

aout_ = aout.copy('F')
ainout_ = ainout.copy('F')
ano_ = ano.copy('F')

def init(ain, aout, ainout, ano, aout_, ainout_, ano_):
    ain.fill(2.0+2.0j)
    aout.fill(0.0+0.0j)
    ainout.fill(34.0+10.0j)
    ano.fill(0.0+0.0j)

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
>>> init(ain, aout, ainout, ano, aout_, ainout_, ano_)
>>> test_results(assumed_shape, (ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
>>> init(ain, aout, ainout, ano, aout_, ainout_, ano_)
>>> test_results(explicit_shape, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
>>> init(ain, aout, ainout, ano, aout_, ainout_, ano_)
>>> test_results(assumed_size, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
'''
