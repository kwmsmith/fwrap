from fwrap_src import pyf_iface as pyf
from fparser import api

from nose.tools import set_trace

def generate_ast(buf):
    ast = []
    block = api.parse(buf.getvalue(), isfree=True, analyze=True)
    tree = block.content
    for proc in tree:
        if proc.blocktype == 'subroutine':
            ast.append(pyf.Subroutine(name=proc.name, args=(pyf.Argument(name="a", dtype=pyf.default_integer, intent='in'),
                                                            pyf.Argument(name="b", dtype=pyf.default_complex, intent='in'),
                                                            pyf.Argument(name="c", dtype=pyf.default_dbl, intent='in')
                                                            )))
        elif proc.blocktype == 'function':
            ast.append(pyf.Function(name=proc.name, args=(), return_type=pyf.default_integer))
        else:
            raise FwrapParseError("unknown fortran construct %r." % proc)
    return ast
