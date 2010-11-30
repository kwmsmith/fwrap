#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------
import re
from fwrap import constants

def mergepyf_ast(cython_ast, cython_ast_from_pyf):
    # Primarily just copy ast, but merge in select detected manual
    # modifications to the pyf file present in pyf_ast

    pyf_procs = dict((proc.name, proc) for proc in cython_ast_from_pyf)
    return [mergepyf_proc(proc, pyf_procs[proc.name])
            for proc in cython_ast]

callstatement_re = re.compile(r'^.*\(\*f2py_func\)\s*\((.*)\).*$')
callstatement_arg_re = re.compile(r'\s*(&)?\s*([a-zA-Z0-9_]+)(\s*\+\s*([a-zA-Z0-9_]+))?\s*$')
callstatement_arg_re = re.compile(r'^\s*(&)?\s*([a-zA-Z0-9_]+)\s*$')

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
        call_args = []
        pyf_arg_names = [arg.name for arg in pyf_proc.call_args]
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
            m = callstatement_arg_re.match(expr)
            if m is not None:
                ampersand, var_name = m.group(1), m.group(2)

                pyf_arg = [arg for arg in pyf_proc.call_args
                           if arg.name == var_name]
                if len(pyf_arg) == 1:
                    # Add the pyf arg we resolved at this position
                    call_args.append(pyf_arg[0].copy())
                    # TODO: Check that type matches f_arg
                    continue # next argument
                else:
                    assert len(pyf_arg) == 0
                    pass # callstatement referred undeclared variable --
                         # fall through to manual handling
            # OK, we do not understand the C code in the callstatement in this
            # argument position, but at least introduce a temporary variable
            # and put in a placeholder for user intervention
            arg = f_arg.copy_and_set(hide_in_wrapper=True,
                                     intent=None,
                                     init_code='##TODO: %s' % expr)
            call_args.append(arg)

        # Reinsert the extra error-handling and function return arguments
        call_args.append(f_proc.call_args[-2].copy())
        call_args.append(f_proc.call_args[-1].copy())

    result = f_proc.copy_and_set(call_args=call_args,
                                 in_args=[arg.copy() for arg in pyf_proc.in_args],
                                 out_args=[arg.copy() for arg in pyf_proc.out_args],
                                 language='pyf')
    return result

def inverse_permutation(permutation):
    result = [None] * len(permutation)
    for idx, p in enumerate(permutation):
        result[p] = idx
    return result
        
    
