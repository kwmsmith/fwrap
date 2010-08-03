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

from fwrap import pyf_iface
from fwrap import gen_config as gc
from fwrap.code import CodeBuffer

from nose.tools import assert_raises, ok_, eq_, set_trace

from tutils import compare

def mock_f2c_types(ctps, *args):
    mp = {'fwrap_default_integer' : 'c_int',
          'fwrap_default_real' : 'c_float',
          'fwrap_default_logical' : 'c_int',
          'fwrap_default_complex' : 'c_float_complex',
          'fwrap_default_character' : 'c_char'
          }
    for ctp in ctps:
        ctp.fc_type = mp[ctp.fwrap_name]

class test_genconfig(object):

    def setup(self):
        self.ctps = [
            gc.ConfigTypeParam(basetype="integer",
                    odecl="integer(kind=kind(0))",
                    fwrap_name="fwrap_default_integer",
                    npy_enum="fwrap_default_integer_enum"),
            gc.ConfigTypeParam(basetype="real",
                    odecl="real(kind=kind(0.0))",
                    fwrap_name="fwrap_default_real",
                    npy_enum="fwrap_default_real_enum"),
            gc.ConfigTypeParam(basetype="logical",
                    odecl="logical(kind=kind(.true.))",
                    fwrap_name="fwrap_default_logical",
                    npy_enum="fwrap_default_logical_enum"),
            gc.ConfigTypeParam(basetype="complex",
                    odecl="complex(kind=kind((0.0,0.0)))",
                    fwrap_name="fwrap_default_complex",
                    npy_enum="fwrap_default_complex_enum"),
            gc.ConfigTypeParam(basetype="character",
                    odecl="character(kind=kind('a'))",
                    fwrap_name="fwrap_default_character",
                    npy_enum="fwrap_default_character_enum")
        ]
        self.int, self.real, self.log, self.cmplx, self.char = self.ctps
        mock_f2c_types(self.ctps)

    def test_gen_f_mod(self):
        eq_(self.int.gen_f_mod(),
                ['integer, parameter :: fwrap_default_integer = c_int'])
        eq_(self.cmplx.gen_f_mod(),
                ['integer, parameter :: '
                    'fwrap_default_complex = c_float_complex'])

    def test_gen_header(self):
        eq_(self.int.gen_c_typedef(), ['typedef int fwrap_default_integer;'])
        eq_(self.cmplx.gen_c_typedef(), ['typedef float _Complex fwrap_default_complex;'])

    def test_gen_pxd(self):
        eq_(self.int.gen_pxd_extern_typedef(),
                ['ctypedef int fwrap_default_integer'])
        eq_(self.cmplx.gen_pxd_extern_typedef(), [])

        eq_(self.int.gen_pxd_intern_typedef(), [])
        eq_(self.cmplx.gen_pxd_intern_typedef(),
                ['ctypedef float complex fwrap_default_complex'])

        eq_(self.int.gen_pxd_extern_extra(), [])
        eq_(self.cmplx.gen_pxd_extern_extra(), [])

    def test_gen_type_spec(self):

        def _compare(ctp_dict, ctp):
            cd = ctp_dict
            x_ = gc.ConfigTypeParam(cd['basetype'],
                            cd['odecl'], cd['fwrap_name'], cd['npy_enum'])
            eq_(x_,y)

        from cPickle import loads
        buf = CodeBuffer()
        gc._generate_type_specs(self.ctps[:2], buf)
        ctps = loads(buf.getvalue())
        for x,y in zip(ctps, self.ctps[:2]):
            _compare(x,y)

        buf = CodeBuffer()
        gc._generate_type_specs(self.ctps[2:], buf)
        ctps = loads(buf.getvalue())
        for x,y in zip(ctps, self.ctps[2:]):
            _compare(x,y)
