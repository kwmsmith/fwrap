#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------
import re

def mergepyf_ast_inplace(cython_ast, cython_ast_from_pyf):
    # Primarily just copy ast, but merge in select detected manual
    # modifications to the pyf file present in pyf_ast

    pyf_procs = dict((proc.name, proc) for proc in cython_ast_from_pyf)
    return [mergepyf_proc_inplace(proc, pyf_procs[proc.name])
            for proc in cython_ast]

callstatement_re = re.compile(r'.*\(\*f2py_func\)\s*\((.*)\).*')
callstatement_arg_re = re.compile(r'\s*(&)?\s*([a-zA-Z0-9_]+)(\s*\+\s*([a-zA-Z0-9_]+))?\s*')

def mergepyf_proc_inplace(proc, pyf_proc):
    proc.merge_comments = []
    callstat = pyf_proc.pyf_callstatement
    result_args = proc.arg_mgr.args
    if callstat is None:
        # Easy, no reordering and arguments should match by position
        pyf_args = pyf_proc.arg_mgr.args
        args_in_extern_order = result_args
    else:
        proc.merge_comments.append('callstatement: %s' % callstat)
        # Hard part: Match up arguments with possible reorderings
        # and renames.
        pyf_arg_names = [arg.get_extern_name() for arg in pyf_proc.arg_mgr.args]
        arg_permutation = []

        m = callstatement_re.match(callstat)
        if m is None:
            raise ValueError('Unable to parse callstatement! Have a look at callstatement_re:' +
                             callstat)

        arg_exprs = m.group(1).split(',')
        for idx, (result_arg, expr), in enumerate(zip(result_args, arg_exprs)):
            m = callstatement_arg_re.match(expr)
            if m is not None:
                ampersand, var_name = m.group(1), m.group(2)
                print m.group(3), m.group(4)
                try:
                    external_idx = pyf_arg_names.index(var_name)
                except ValueError:
                    print var_name, pyf_arg_names
                    1/0
                    pass # name mismatch -- fall through to manual handling
                else:
                    # OK, is a simple argument reordering/rename
                    result_arg.set_extern_name(var_name)
                    arg_permutation.append(external_idx)
                    continue # done here
                    
            # Introduce temporary variable
            1/0
        print arg_permutation
        args_in_extern_order = [result_args[idx]
                                  for idx in inverse_permutation(arg_permutation)]

        pyf_args = pyf_proc.arg_mgr.args

    proc.arg_mgr.args_in_extern_order = args_in_extern_order

    for arg, pyf_arg in zip(result_args, pyf_args):
        arg.intent = pyf_arg.intent
        arg.init_code = pyf_arg.init_code
        arg.hide_in_wrapper = pyf_arg.hide_in_wrapper
        arg.check = pyf_arg.check
        arg.pyf_mode = True # refactor
         
    return proc

def inverse_permutation(permutation):
    result = [None] * len(permutation)
    for idx, p in enumerate(permutation):
        result[p] = idx
    return result
        
    
