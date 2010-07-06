from all_char_arrays_fwrap import *
import numpy as np

ll, n1, n2 = 6, 3, 4
ain = np.empty((n1,n2), dtype='S%d' % ll, order='F')
aout = ain.copy('F')
ainout = ain.copy('F')
ano = ain.copy('F')

aout_ = aout.copy('F')
ainout_ = ainout.copy('F')
ano_ = ano.copy('F')

def init(ain, aout, ainout, ano, aout_, ainout_, ano_):
    ain.fill('ABCDEF')
    aout.fill('      ')
    ainout.fill('123456')
    ano.fill('      ')

    aout_[...] = ain
    ano_[...] = ainout
    ainout_.fill(ain[0,0][:3] + ano_[0,0][3:])

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
>>> test_results(explicit_shape, (ll, n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
>>> init(ain, aout, ainout, ano, aout_, ainout_, ano_)
>>> test_results(assumed_size, (n1, n2, ain, aout, ainout, ano), (aout_, ainout_, ano_))
True
'''
