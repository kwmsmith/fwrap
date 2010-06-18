from cPickle import dumps
from fwrap_src import pyf_iface
import constants

NON_ERR_LABEL = 200
ERR_LABEL = 100

def generate_type_specs(ast, buf):
    ctps = extract_ctps(ast)
    _generate_type_specs(ctps, buf)

def _generate_type_specs(ctps, buf):
    out_lst = []
    for ctp in ctps:
        out_lst.append(dict(basetype=ctp.basetype,
                            odecl=ctp.odecl,
                            fwrap_name=ctp.fwrap_name))
    buf.write(dumps(out_lst))

class ConfigTypeParam(object):

    def __init__(self, basetype, odecl, fwrap_name):
        self.basetype = basetype
        self.odecl = odecl
        self.fwrap_name = fwrap_name
        self.c_type = None

    @classmethod
    def from_dtypes(cls, dtypes):
        ret = []
        for dtype in dtypes:
            if dtype.odecl is None:
                continue
            ret.append(cls(basetype=dtype.type,
                           fwrap_name=dtype.fw_ktp,
                           odecl=dtype.odecl))
        return ret

    def __eq__(self, other):
        return self.basetype == other.basetype and \
                self.odecl == other.odecl and \
                self.fwrap_name == other.fwrap_name

    def gen_f_mod(self):
        if self.c_type is None:
            raise RuntimeError("c_type is None, unable to generate fortran type information.")
        return ['integer, parameter :: %s = %s' % (self.fwrap_name, self.c_type)]

def extract_ctps(ast):
    dtypes = set()
    for proc in ast:
        dtypes.update(proc.all_dtypes())
    dtypes = list(dtypes)
    return ConfigTypeParam.from_dtypes(dtypes)

class GenConfigException(Exception):
    pass
