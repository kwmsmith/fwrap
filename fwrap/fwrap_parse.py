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

from fwrap import pyf_iface as pyf
from fparser import api

def generate_ast(fsrcs):
    ast = []
    for src in fsrcs:
        block = api.parse(src, analyze=True)
        tree = block.content
        for proc in tree:

            if not is_proc(proc):
                raise RuntimeError(
                        "unsupported Fortran construct %r." % proc)

            args = _get_args(proc)
            params = _get_params(proc)

            if proc.blocktype == 'subroutine':
                ast.append(pyf.Subroutine(
                                name=proc.name,
                                args=args,
                                params=params))
            elif proc.blocktype == 'function':
                ast.append(pyf.Function(
                                name=proc.name,
                                args=args,
                                params=params,
                                return_arg=_get_ret_arg(proc)))
    return ast


def is_proc(proc):
    return proc.blocktype in ('subroutine', 'function')

def _get_ret_arg(proc):
    ret_var = proc.get_variable(proc.result)
    ret_arg = _get_arg(ret_var)
    ret_arg.intent = None
    return ret_arg

def _get_param(p_param):
    if not p_param.is_parameter():
        raise ValueError("argument %r is not a parameter" % p_param)
    if not p_param.init:
        raise ValueError("parameter %r does not have an initialization "
                         "expression." % p_param)
    p_typedecl = p_param.get_typedecl()
    dtype = _get_dtype(p_typedecl)
    name = p_param.name
    intent = _get_intent(p_param)
    if not p_param.is_scalar():
        raise RuntimeError("do not support array or derived-type "
                           "parameters at the moment...")
    return pyf.Parameter(name=name, dtype=dtype, expr=p_param.init)

def _get_arg(p_arg):
    p_typedecl = p_arg.get_typedecl()
    dtype = _get_dtype(p_typedecl)
    name = p_arg.name
    intent = _get_intent(p_arg)
    if p_arg.is_scalar():
        return pyf.Argument(name=name, dtype=dtype, intent=intent)
    elif p_arg.is_array():
        p_dims = p_arg.get_array_spec()
        dimspec = pyf.Dimension(p_dims)
        return pyf.Argument(name=name,
                dtype=dtype, intent=intent, dimension=dimspec)
    else:
        raise RuntimeError(
                "argument %s is neither "
                    "a scalar or an array (derived type?)" % p_arg)

def _get_args(proc):
    args = []
    for argname in proc.args:
        p_arg = proc.get_variable(argname)
        args.append(_get_arg(p_arg))
    return args

def _get_params(proc):
    params = []
    for varname in proc.a.variables:
        var = proc.a.variables[varname]
        if var.is_parameter():
            params.append(_get_param(var))
    return params

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
        raise RuntimeError(
                "argument has multiple "
                    "intents specified, '%s', %s" % (arg, intents))
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
        raise RuntimeError(
                "only intrinsic types supported ATM... [%s]" % str(typedecl))
    length, kind = typedecl.selector
    if not kind and not length:
        return name2default[typedecl.name]
    if length and kind and typedecl.name != 'character':
        raise RuntimeError("both length and kind specified for "
                               "non-character intrinsic type: "
                               "length: %s kind: %s" % (length, kind))
    if typedecl.name == 'character':
        if length == '*':
            fw_ktp = '%s_xX' % (typedecl.name)
        else:
            fw_ktp = '%s_x%s' % (typedecl.name, length)
        return pyf.CharacterType(fw_ktp=fw_ktp,
                        len=length, kind=kind)
    if length and not kind:
        return name2type[typedecl.name](fw_ktp="%s_x%s" %
                (typedecl.name, length),
                length=length)
    try:
        int(kind)
    except ValueError:
        raise RuntimeError(
                "only integer constant kind "
                    "parameters supported ATM, given '%s'" % kind)
    if typedecl.name == 'doubleprecision':
        return pyf.default_dbl
    return name2type[typedecl.name](fw_ktp="%s_%s" %
            (typedecl.name, kind), kind=kind)
