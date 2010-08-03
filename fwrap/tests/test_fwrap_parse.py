#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Fwrap project nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#------------------------------------------------------------------------------

from fwrap import fwrap_parse as fp
from fwrap import pyf_iface as pyf

from cStringIO import StringIO

from nose.tools import ok_, eq_, set_trace

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

def test_parse_array_args():
    buf = '''\
      SUBROUTINE DGESDD( JOBZ, M, N, A, LDA, S, U, LDU, VT, LDVT, WORK,
     $                   LWORK, IWORK, INFO )
*
*  -- LAPACK driver routine (version 3.2.1)                                  --
*  -- LAPACK is a software package provided by Univ. of Tennessee,    --
*  -- Univ. of California Berkeley, Univ. of Colorado Denver and NAG Ltd..--
*     March 2009
*
*     .. Scalar Arguments ..
      CHARACTER          JOBZ
      INTEGER            INFO, LDA, LDU, LDVT, LWORK, M, N
*     ..
*     .. Array Arguments ..
      INTEGER            IWORK( * )
      DOUBLE PRECISION   A( LDA, * ), S( * ), U( LDU, * ),
     $                   VT( LDVT, * ), WORK( * )
      END SUBROUTINE DGESDD'''
    subr = fp.generate_ast([buf])[0]
    eq_(subr.name, 'dgesdd')
    eq_([arg.name for arg in subr.args],
        "jobz m n a lda s u ldu vt ldvt work lwork iwork info".split())

def test_parse_kind_args():
    fcode = '''\
function int_args_func(a,b,c,d)
      integer(kind=8) :: int_args_func
      integer(kind=1), intent(in) :: a
      integer(kind=2), intent(in) :: b
      integer(kind=4), intent(in) :: c
      integer(kind=8), intent(out) :: d

      d = a + b + c
      int_args_func = 10

end function int_args_func
'''
    func = fp.generate_ast([fcode])[0]
    eq_([arg.dtype.odecl
            for arg in func.args],
        ["integer(kind=%d)" % i
            for i in (1,2,4,8)])
