from fwrap import pyf_iface as pyf
from fparser import api

from nose.tools import set_trace

def generate_ast(fsrcs):
    ast = []
    for src in fsrcs:
        block = api.parse(src, analyze=True)
        tree = block.content
        for proc in tree:
            if is_proc(proc):
                fargs = _get_args(proc)
            if proc.blocktype == 'subroutine':
                ast.append(pyf.Subroutine(name=proc.name, args=fargs))
            elif proc.blocktype == 'function':
                ret_type = get_rettype(proc)
                ast.append(pyf.Function(name=proc.name, args=fargs,
                    return_type=pyf.default_integer))
            else:
                raise RuntimeError("unsupported Fortran construct %r." % proc)
    return ast


def is_proc(proc):
    return proc.blocktype in ('subroutine', 'function')

def get_rettype(proc):
    ret_var = proc.get_variable(proc.result)
    return _get_dtype(ret_var.get_typedecl())

def _get_args(proc):
    args = []
    for argname in proc.args:
        p_arg = proc.get_variable(argname)
        p_typedecl = p_arg.get_typedecl()
        dtype = _get_dtype(p_typedecl)
        name = p_arg.name
        intent = _get_intent(p_arg)
        if p_arg.is_scalar():
            args.append(pyf.Argument(name=name, dtype=dtype, intent=intent))
        elif p_arg.is_array():
            p_dims = p_arg.get_array_spec()
            dims = []
            for dim in p_dims:
                if dim == ('',''):
                    dims.append(':')
                elif len(dim) == 1:
                    dims.append(dim[0])
                else:
                    raise RuntimeError("can't handle dimension(x:y) declarations yet...")
            args.append(pyf.Argument(name=name, dtype=dtype, intent=intent, dimension=dims))
        else:
            raise RuntimeError("argument %s is neither a scalar or an array (derived type?)" % p_arg)
    return args

def _get_intent(arg):
    intents = []
    if not arg.intent:
        intents.append("inout")
    else:
        if arg.is_intent_in():
            intents.append("in")
        if arg.is_intent_inout():
            intents.append("inout")
        if arg.is_intent_out():
            intents.append("out")
    if not intents:
        raise RuntimeError("argument has no intent specified, '%s'" % arg)
    if len(intents) > 1:
        raise RuntimeError("argument has multiple intents specified, '%s', %s" % (arg, intents))
    return intents[0]

name2default = {
        'integer' : pyf.default_integer,
        'real'    : pyf.default_real,
        'doubleprecision' : pyf.default_dbl,
        'complex' : pyf.default_complex,
        'character' : pyf.default_character,
        'logical' : pyf.default_logical,
        }

name2type = {
        'integer' : pyf.IntegerType,
        'real' : pyf.RealType,
        'complex' : pyf.ComplexType,
        'character' : pyf.CharacterType,
        'logical' : pyf.LogicalType,
        }

def _get_dtype(typedecl):
    if not typedecl.is_intrinsic():
        raise RuntimeError("only intrinsic types supported ATM... [%s]" % str(typedecl))
    length, kind = typedecl.selector
    if not kind and not length:
        return name2default[typedecl.name]
    if length and kind and typedecl.name != 'character':
        raise RuntimeError("both length and kind specified for"
                           " non-character intrinsic type: length: %s kind: %s" % (length, kind))
    if typedecl.name == 'character':
        if length == '*':
            fw_ktp = '%s_xX' % (typedecl.name)
        else:
            fw_ktp = '%s_x%s' % (typedecl.name, length)
        return pyf.CharacterType(fw_ktp=fw_ktp, odecl=typedecl.tostr().lower(), len=length)
    if length and not kind:
        return name2type[typedecl.name](fw_ktp="%s_x%s" % (typedecl.name, length), odecl=typedecl.tostr().lower())
    try:
        int(kind)
    except ValueError:
        raise RuntimeError("only integer constant kind parameters supported ATM, given '%s'" % kind)
    if typedecl.name == 'doubleprecision':
        return pyf.default_dbl
    return name2type[typedecl.name](fw_ktp="%s_%s" % (typedecl.name, kind), odecl=typedecl.tostr().lower())
