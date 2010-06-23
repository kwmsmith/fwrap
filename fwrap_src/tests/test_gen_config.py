from fwrap_src import pyf_iface
from fwrap_src import gen_config as gc
from fwrap_src.code import CodeBuffer

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
                    odecl="integer(kind(0))",
                    fwrap_name="fwrap_default_integer"),
            gc.ConfigTypeParam(basetype="real",
                    odecl="real(kind(0.0))",
                    fwrap_name="fwrap_default_real"),
            gc.ConfigTypeParam(basetype="logical",
                    odecl="logical(kind(.true.))",
                    fwrap_name="fwrap_default_logical"),
            gc.ConfigTypeParam(basetype="complex",
                    odecl="complex(kind((0.0,0.0)))",
                    fwrap_name="fwrap_default_complex"),
            gc.ConfigTypeParam(basetype="character",
                    odecl="character(kind=kind('a'))",
                    fwrap_name="fwrap_default_character")
        ]
        self.int, self.real, self.log, self.cmplx, self.char = self.ctps
        mock_f2c_types(self.ctps)

    def test_gen_f_mod(self):
        eq_(self.int.gen_f_mod(), ['integer, parameter :: fwrap_default_integer = c_int'])
        eq_(self.cmplx.gen_f_mod(), ['integer, parameter :: fwrap_default_complex = c_float_complex'])

    def test_gen_header(self):
        eq_(self.int.gen_c_includes(), [])
        eq_(self.int.gen_c_typedef(), ['typedef int fwrap_default_integer;'])
        eq_(self.int.gen_c_extra(), [])
        eq_(self.cmplx.gen_c_typedef(),
                ['typedef float _Complex fwrap_default_complex;'])
        eq_(self.cmplx.gen_c_includes(), ['#include <complex.h>'])
        eq_(self.cmplx.gen_c_extra(),
                 ("#define %(ktp)s_creal(x) (creal(x))\n"
                  "#define %(ktp)s_cimag(x) (cimag(x))\n"
                  "#define %(ktp)s_from_parts(r, i, x)"
                  " (x = ((r) + _Complex_I * (i)))" % {'ktp' : self.cmplx.fwrap_name}).splitlines())

    def test_gen_pxd(self):
        eq_(self.int.gen_pxd_extern_typedef(), ['ctypedef int fwrap_default_integer'])
        eq_(self.cmplx.gen_pxd_extern_typedef(), ['ctypedef float fwrap_default_complex'])

        eq_(self.int.gen_pxd_intern_typedef(), [])
        eq_(self.cmplx.gen_pxd_intern_typedef(), ['ctypedef float complex cy_fwrap_default_complex'])

        eq_(self.int.gen_pxd_extern_extra(), [])
        eq_(self.cmplx.gen_pxd_extern_extra(),
            ['float fwrap_default_complex_creal(fwrap_default_complex fdc)',
             'float fwrap_default_complex_cimag(fwrap_default_complex fdc)',
             'void fwrap_default_complex_from_parts(float r, float i, fwrap_default_complex fc)']
            )

    def test_gen_type_spec(self):

        def _compare(ctp_dict, ctp):
            cd = ctp_dict
            x_ = gc.ConfigTypeParam(cd['basetype'], cd['odecl'], cd['fwrap_name'])
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
