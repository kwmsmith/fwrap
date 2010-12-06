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

    def f(s):
        print s
        e = CToCython().translate(s)
        deps = list(e.requires)
        deps.sort()
        return e.template, ','.join(deps)
    
    eq_(f(' ((int)a>=3) && !(b!=c) || (e<f)'),
        ('(<int>%(a)s >= 3) and not (%(b)s != %(c)s) or (%(e)s < %(f)s)', 'a,b,c,e,f'))
    eq_(f('len(  by ) + z'), ('np.PyArray_DIMS(%(by)s)[0] + %(z)s', 'by,z'))

    eq_(f('3.45'), ('3.45', ''))

    eq_(f('a==2?"b":c'),
        ('"b" if (%(a)s == 2) else %(c)s', 'a,c'))
    eq_(f('(a>=2?x : y)?"b":c')[0], '"b" if (%(x)s if (%(a)s >= 2) else %(y)s) else %(c)s')
    eq_(f('(a > 10)?"A":"B"')[0], '"A" if (%(a)s > 10) else "B"')

    eq_(f('a ? b : c')[0], '%(b)s if %(a)s else %(c)s')
    eq_(f('a == 3 ? b : c')[0], '%(b)s if (%(a)s == 3) else %(c)s')


    eq_(f('trans!=0&&x==y ? (trans == 1 ? a : !b) : (int)c')[0],
        '(%(a)s if (%(trans)s == 1) else not %(b)s) if ((%(trans)s != 0) '
        'and (%(x)s == %(y)s)) else <int>%(c)s')
    eq_(f(' a||b || c==d/3||d &&e&&f')[0],
        '%(a)s or %(b)s or (%(c)s == (%(d)s // 3)) or %(d)s and %(e)s and %(f)s')
    eq_(f('trans!=0&&x==y+1 ? (trans == 1 ? len(a) : !b) : (int)c'),
        ('(np.PyArray_DIMS(%(a)s)[0] if (%(trans)s == 1) else not %(b)s) '
         'if ((%(trans)s != 0) and (%(x)s == (%(y)s + 1))) else <int>%(c)s',
         'a,b,c,trans,x,y'))
    eq_(f('shape(x, 1)'), ('np.PyArray_DIMS(%(x)s)[1]', 'x'))
    eq_(f('abs(x)'), ('abs(%(x)s)', 'x'))
    eq_(f('incx==1||incx==-1'), ('(%(incx)s == 1) or (%(incx)s == -1)', 'incx'))
