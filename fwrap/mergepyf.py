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

callstatement_re = re.compile(r'\(*f2py_func\)\((.*)\)')
callstatement_arg_re = re.compile(r'\s*&\s*([a-zA-Z0-9_])\s*')

def mergepyf_proc_inplace(proc, pyf_proc):
    proc.merge_comments = []
    callstat = pyf_proc.wrapped.wrapped.pyf_callstatement
    if callstat is None:
        # Easy, no reordering and arguments should match by position
        proc.arg_mgr.external_argument_order = proc.arg_mgr.args
        pyf_args = pyf_proc.arg_mgr.args
    else:
        proc.merge_comments.append('callstatement: %s' % callstat)
        # Hard part: Match up arguments with possible reorderings
        # and renames.
        1/0

    for arg, pyf_arg in zip(proc.arg_mgr.args, pyf_args):
        arg.intent = pyf_arg.intent
        arg.init_code = pyf_arg.init_code
        arg.hide_in_wrapper = pyf_arg.hide_in_wrapper
        arg.check = pyf_arg.check
        arg.pyf_mode = True # refactor
         
    return proc

    def get_name(arg):
        if hasattr(arg, 'extern_name'):
            return arg.extern_name
        else:
            return arg.name

    

##     m = callstatement_re.match(callstat)
##     if m is None:
##         raise ValueError('Unable to parse callstatement! Have a look at callstatement_re.')

##     call_permutation = [None] * len(proc.arg_mgr.args)
    
##     arg_exprs = m.group(1).split(',')
##     for idx, expr in enumerate(arg_exprs):
##         m = callstatement_arg_re.match(expr)
##         if m is None:
##             pyf_proc.merge_comment('Handle call argument #%d manually: %s' % (idx, expr))
##         else:
##             #
##             call_permutation = 
##         varname = 
            
    
        
        
    return
    from pprint import pprint
    for a, b in zip(pyf_proc.arg_mgr.args,
                    proc.arg_mgr.args):
        print get_name(a), get_name(b)
    print '---'
#    pprint( [arg.__dict__ for arg in pyf_proc.arg_mgr.args])
#    pprint( [arg.__dict__ for arg in proc.arg_mgr.args])

    
##     name_to_fproc = dict((proc.name, proc) for proc in ast)
##     ordering = dict((proc.name, idx) for idx, proc in enumerate(ast))
##     fproc_names = set(name_to_fproc.keys())

##     result = []
##     for proc in pyf_ast:
##         if proc.name in fproc_names:
##             result.append(proc)
##         else:
##             warn('Procedure %s present in pyf but not in Fortran source, dropping it' %
##                  proc.name)
##     result.sort(key=lambda x: ordering[x.name])
##     for pyf_proc in result:
##         mergepyf_proc_inplace(pyf_proc, name_to_fproc[pyf_proc.name])
##     return result
