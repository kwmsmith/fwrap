from fwrap_src import fwrap_parse as fp
from fwrap_src import pyf_iface as pyf

from cStringIO import StringIO

from nose.tools import ok_, eq_

def test_parse_many():
    buf = '''\
subroutine subr1(a, b, c)
implicit none
integer, intent(in) :: a
complex :: b
double precision, intent(out) :: c

c = a + aimag(b)

end subroutine subr1


function func1(a, b, c)
implicit none
integer, intent(in) :: a
real :: b
complex, intent(in) :: c
double precision :: func1

func1 = a + aimag(c) - b

end function func1
'''
    subr, func = fp.generate_ast([buf])
    eq_(subr.name, 'subr1')
    eq_(func.name, 'func1')
    eq_([arg.name for arg in subr.args], ['a', 'b', 'c'])
    eq_([arg.dtype for arg in subr.args], [pyf.default_integer,
                                           pyf.default_complex,
                                           pyf.default_dbl])
    # eq_([arg.name for arg in subr.args], ['a', 'b', 'c'])
