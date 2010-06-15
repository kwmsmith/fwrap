from fwrap_src import pyf_iface
from fwrap_src import gen_config as gc
from fwrap_src.code import CodeBuffer

from nose.tools import assert_raises, ok_, eq_, set_trace

from tutils import compare

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

    def test_gen_type_spec(self):

        def _compare(ctp_dict, ctp):
            cd = ctp_dict
            x_ = gc.ConfigTypeParam(cd['basetype'], cd['type_decl'], cd['fwrap_name'])
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
