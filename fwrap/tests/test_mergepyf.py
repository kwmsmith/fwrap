#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import code

from nose.tools import (ok_, eq_, set_trace, raises, assert_raises,
                        assert_false, assert_true)
import sys
from pprint import pprint
from textwrap import dedent
from fwrap.mergepyf import *
from StringIO import StringIO

def test_expressions():

    def f(s, varmap=None):
        print s
        r, vs = CToCython(variable_map).translate(s)
        vs = list(vs)
        vs.sort()
        return r, ','.join(vs)
    
    eq_(f(' ((int)a>=3) && !(b!=c) || (e<f)'),
        ('(<int>a >= 3) and not (b != c) or (e < f)', 'a,b,c,e,f'))
    eq_(f('len(  by ) + z'), ('np.PyArray_DIMS(by__)[0] + z', 'by,z'))

    eq_(f('3.45'), ('3.45', ''))

    eq_(f('a==2?"b":c'),
        ('"b" if (a == 2) else c', 'a,c'))
    eq_(f('(a>=2?x : y)?"b":c')[0], '"b" if (x if (a >= 2) else y) else c')
    eq_(f('(a > 10)?"A":"B"')[0], '"A" if (a > 10) else "B"')

    eq_(f('a ? b : c')[0], 'b if a else c')
    eq_(f('a == 3 ? b : c')[0], 'b if (a == 3) else c')


    eq_(f('trans!=0&&x==y ? (trans == 1 ? a : !b) : (int)c')[0],
        '(a if (trans == 1) else not b) if ((trans != 0) and (x == y)) else <int>c')
    eq_(f(' a||b || c==d/3||d &&e&&f')[0], 'a or b or (c == (d // 3)) or d and e and f')
    eq_(f('trans!=0&&x==y+1 ? (trans == 1 ? len(a) : !b) : (int)c'),
        ('(np.PyArray_DIMS(a)[0] if (trans == 1) else not b) '
         'if ((trans != 0) and (x == (y + 1))) else <int>c',
         'a,b,c,trans,x,y'))
    # Variable sub:
    eq_(f('shape(x, 1)', {'x':'foo'}), ('np.PyArray_DIMS(foo)[1]', 'x'))


