#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------
import re
from fwrap import constants
from fwrap.pyf_iface import _py_kw_mangler, py_kw_mangle_expression
from fwrap.cy_wrap import _CyArg

def mergepyf_ast(cython_ast, cython_ast_from_pyf):
    # Primarily just copy ast, but merge in select detected manual
    # modifications to the pyf file present in pyf_ast

    pyf_procs = dict((proc.name, proc) for proc in cython_ast_from_pyf)
    return [mergepyf_proc(proc, pyf_procs[proc.name])
            for proc in cython_ast]

callstatement_re = re.compile(r'^.*\(\*f2py_func\)\s*\((.*)\).*$')
callstatement_arg_re = re.compile(r'\s*(&)?\s*([a-zA-Z0-9_]+)(\s*\+\s*([a-zA-Z0-9_]+))?\s*$')

def mergepyf_proc(f_proc, pyf_proc):
    #merge_comments = []
    # There are three argument lists to merge:
    # call_args: "proc" definitely has the right one, however we
    #            may want to rename arguments
    # in_args: pyf_proc has the right one
    # out_args: pyf_proc has the right one
    #
    # Try to parse call_statement to figure out as much as
    # possible, and leave the rest to the user.

#    print
#    print '================', f_proc.name, '===================='
    
    callstat = pyf_proc.pyf_callstatement
    if callstat is None:
        # We can simply use the pyf argument list and be satisfied
        if len(f_proc.call_args) != len(pyf_proc.call_args):
            raise ValueError('pyf and f description of function is different')
        # TODO: Verify that types match as well
        call_args = [arg.copy() for arg in pyf_proc.call_args]
    else:
        # Do NOT trust the name or order in pyf_proc.call_args,
        # but match arguments by their position in the callstatement
        pyf_args = pyf_proc.call_args + pyf_proc.aux_args
        call_args = []
        m = callstatement_re.match(callstat)
        if m is None:
            raise ValueError('Unable to parse callstatement! Have a look at callstatement_re:' +
                             callstat)
        arg_exprs = m.group(1).split(',')

        assert f_proc.call_args[-2].name == constants.ERR_NAME
        assert f_proc.call_args[-1].name == constants.ERRSTR_NAME
        fortran_args = f_proc.call_args[:-2]
        if f_proc.kind == 'function':
            assert f_proc.call_args[0].name == constants.RETURN_ARG_NAME
            call_args.append(f_proc.call_args[0].copy())
            fortran_args = fortran_args[1:]

        for idx, (f_arg, expr) in enumerate(zip(fortran_args, arg_exprs)):
            arg = parse_callstatement_arg(expr, pyf_args)
            if arg is None:
                # OK, we do not understand the C code in the callstatement in this
                # argument position, but at least introduce a temporary variable
                # and put in a placeholder for user intervention
                arg = f_arg.copy_and_set(
                    intent=None,
                    pyf_hide=True,
                    pyf_default_value='##TODO: %s' % expr)
            call_args.append(arg)
            
        # Reinsert the extra error-handling and function return arguments
        call_args.append(f_proc.call_args[-2].copy())
        call_args.append(f_proc.call_args[-1].copy())

    # Make sure our three lists (in/out/callargs) contain the same
    # argument objects
    all_args = dict((arg.name, arg) for arg in call_args)
    def copy_or_get(arg):
        result = all_args.get(arg.name, None)
        if result is None:
            result = arg.copy()
        return result

    in_args = [copy_or_get(arg) for arg in pyf_proc.in_args]
    out_args = [copy_or_get(arg) for arg in pyf_proc.out_args]
    in_args = process_in_args(in_args)
    result = f_proc.copy_and_set(call_args=call_args,
                                 in_args=in_args,
                                 out_args=out_args,
                                 aux_args=pyf_proc.aux_args,
                                 language='pyf')
#    print result
    return result

def parse_callstatement_arg(arg_expr, pyf_args):
    # Parse arg_expr, and return a suitable new argument based on pyf_args
    # Returns None for unparseable/too complex expression
    m = callstatement_arg_re.match(arg_expr)
    if m is not None:
        ampersand, var_name, offset = m.group(1), m.group(2), m.group(4)
        if offset is not None and ampersand is not None:
            raise ValueError('Arithmetic on scalar pointer?')
        pyf_arg = [arg for arg in pyf_args if arg.name == var_name]
        if len(pyf_arg) >= 1:
            result = pyf_arg[0].copy()
            if offset is not None:
                if not result.is_array:
                    raise ValueError('Passing scalar without taking address?')
                result.update(mem_offset_code=_py_kw_mangler(offset))
            return result
        else:
            return None
    else:
        return None

literal_re = re.compile(r'^-?[0-9.]+$') # close enough

def process_in_args(in_args):
    # Arguments must be changed as follows:
    # a) Reorder so that arguments with defaults come last
    # b) Parse the default_value into something usable by Cython.
    for arg in in_args:
        if arg.pyf_check is not None:
            arg.update(pyf_check=[c_to_cython(c) for c in arg.pyf_check])
    
    mandatory = [arg for arg in in_args if not arg.is_optional()]
    optional = [arg for arg in in_args if arg.is_optional()]
    in_args = mandatory + optional

    for arg in optional:
        default_value = arg.pyf_default_value
        if (default_value is not None and
            literal_re.match(default_value) is None):
            # Do some crude processing of default_value to translate
            # it fully or partially to Cython
            default_value = (default_value)
            default_value = c_to_cython(default_value)
            arg.update(defer_init_to_body=True,
                       pyf_default_value=default_value)

    
    # Process intent(copy) and intent(overwrite). f2py behaviour is to
    # add overwrite_X to the very end of the argument list, so insert
    # new argument nodes.
    overwrite_args = []
    for arg in in_args:
        if arg.pyf_overwrite_flag:
            flagname = 'overwrite_%s' % arg.cy_name
            arg.overwrite_flag_cy_name = flagname
            overwrite_args.append(
                _CyArg(name=flagname,
                       cy_name=flagname,
                       ktp='bint',
                       intent='in',
                       dtype=None,
                       pyf_default_value=repr(arg.pyf_overwrite_flag_default)))
    in_args.extend(overwrite_args)

    # Return new set of in_args
    return in_args

_c_to_cython_dictionary = {
    '&&' : 'and',
    '||' : 'or',
    '!' : 'not',
    '/' : '//', # ...probably...
    # Just to 'convert' whitespace style as well, include
    # other operators
    '<' : '<',
    '<=' : '<=',
    '==' : '==',
    '>=' : '>=',
    '>' : '>',
    '!=' : '!=',
    '+' : '+',
    '-' : '-',
    '*' : '*'
}

# Add spaces
for key, value in _c_to_cython_dictionary.iteritems():
    _c_to_cython_dictionary[key] = ' %s ' % value

cast_re = re.compile(r'\((int|float|double)\)([a-zA-Z0-9_]+)')
functions_re = re.compile(r'(len)\(\s*([a-zA-Z0-9_]+)\s*\)')
whitespace_re = re.compile(r'\s\s+')
operators_re = re.compile(r'&&|\|\||<=?|>=?|==|!=?')

def c_to_cython(expr):
    # Deal with the most common cases to reduce the amount
    # of manual modification needed afterwards. This is used
    # in check(...), so support common boolean constructs
    expr = py_kw_mangle_expression(expr)
    
    def f(m):
        return _c_to_cython_dictionary[m.group(0)]

    expr = operators_re.sub(f, expr)
    expr = whitespace_re.sub(' ', expr) # Remove redundant spaces introduced
    expr = cast_re.sub(r'<\1>\2', expr) # (int)v -> <int>v

    def funcs(m):
        func = m.group(1)
        if func == 'len':
            return 'np.PyArray_DIMS(%s)[0]' % m.group(2)
        else:
            assert False
    
    expr = functions_re.sub(funcs, expr)
    return expr.strip()

