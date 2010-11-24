#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

#
# Currently only deduplicates contents of Cython pyx files
#

import re
from fwrap import cy_wrap

#
# Utilities
#
unique = object()
def all_same(iterable):
    return reduce(lambda x, y: x if x is y else unique, iterable) is not unique

def all_equal(iterable):
    return reduce(lambda x, y: x if x == y else unique, iterable) is not unique


#
# Detect templates and insert them into an ast
#

class UnableToMergeError(Exception):
    pass

def cy_deduplify(cy_ast, cfg):
    name_to_proc = dict((proc.name, proc) for proc in cy_ast)
    procnames = name_to_proc.keys()
    groups = find_candidate_groups_by_name(procnames)

    print cy_ast
    for names_in_group in groups:
        procs = [name_to_proc[name] for name in names_in_group]
        try:
            template_node = cy_create_template(procs, cfg)
        except UnableToMergeError:
            continue
        # Insert the created template at the position
        # of the *first* routine, and remove the other
        # routines
        to_sub = names_in_group[0]
        to_remove = names_in_group[1:]
        cy_ast = [(template_node if node.name == to_sub else node)
                  for node in cy_ast
                  if node.name not in to_remove]
    print cy_ast
    return cy_ast

def cy_create_template(procs, cfg):
    """Make an attempt to merge the given procedures into a template
    """
    arg_lists = [proc.arg_mgr.args for proc in procs]
    if not all_equal(len(lst) for lst in arg_lists):
        # Different number of arguments
        raise UnableToMergeError()
    for matched_args in zip(*arg_lists):
        arg0 = matched_args[0]
        for arg in matched_args[1:]:
            if not arg0.equal_up_to_type(arg):
                raise UnableToMergeError()
    return TemplatedProcedure(procs, cfg)

blas_re = re.compile(r'^([sdcz])([a-z0-9_]+)$')

def find_candidate_groups_by_name(names):
    """Find candidate groups of procedures by inspecting procedure name

    For now, just use BLAS/LAPACK conventions. TODO: Pluggable API for this?
    
    Input:
    List of procedure names
    
    Output:
    
    List of possible template groups, [[a, b], [c, d, e], ...]
    Routines not in a template group should not be present in the output.
    Templates rules will contain the order listed in output
    (currently, reorders in the sX, dX, cX, zX order).
    """
    groups = {}
    
    for name in names:
        m = blas_re.match(name)
        if m is not None:
            stem = m.group(2)
            lst = groups.get(stem, None)
            if lst is None:
                lst = groups[stem] = []
            lst.append(name)

    result = []
    for stem, proclst in groups.iteritems():
        if len(proclst) > 1:
            assert len(proclst) <= 4
            proclst.sort(key=lambda name: 'sdcz'.index(name[0]))
            result.append(proclst)

    return result
    
#
# Template ast nodes for pyx files
#

class TemplatedCyArrayArg(cy_wrap._CyArrayArgWrapper):
    def __init__(self, args, template_mgr):
        cy_wrap._CyArrayArgWrapper.__init__(self, args[0].arg)

        for merge_attr in ('ktp', 'py_type_name', 'npy_enum'):
            values = [getattr(arg, merge_attr) for arg in args]
            code = template_mgr.get_code_for_values(values, merge_attr)
            setattr(self, merge_attr, code)

#        self.args = args
#        self.template_mgr = template_mgr
        
        # If names are not all the same we must use a template for it
        # TODO: Just assume this for now
##         if 0:
##             names = [arg.name for arg in args]
##             if all(names[0] == x for x in names[1:]):
##                 self.name = names[0]
##             else:
##                 self.name = template_mgr.get_variable_code(
##                     template_mgr.add_variable(names))

def get_templated_cy_arg_wrapper(args, template_mgr):
    assert all_same(type(x) for x in args)
    cls = type(args[0])
    if cls is cy_wrap._CyArrayArgWrapper:
        return TemplatedCyArrayArg(args, template_mgr)
    else:
        print 'warning'
        return args[0]

class TemplatedProcedure(cy_wrap.ProcWrapper):

    def __init__(self, procs, cfg):
        cy_wrap.ProcWrapper.__init__(self, procs[0].wrapped)
        self.template_mgr = create_template_manager(cfg)

        self.procs = procs
        self.names = [proc.name for proc in procs]
        self.name = self.template_mgr.get_code_for_values(self.names, 'procname')
        
        merged_args = [get_templated_cy_arg_wrapper(matched_args,
                                                     self.template_mgr)
                       for matched_args in
                       zip(*[proc.arg_mgr.args for proc in procs])]
        self.arg_mgr = cy_wrap.CyArgWrapperManager(merged_args)
        self.wrapped_name = self.template_mgr.get_code_for_values(
            (proc.wrapped_name for proc in procs), 'wrapped')

    def generate_wrapper(self, ctx, buf):
        self.template_mgr.put_start_loop(buf)
        cy_wrap.ProcWrapper.generate_wrapper(self, ctx, buf)
        self.template_mgr.put_end_loop(buf)

    def get_names(self):
        return [proc.name for proc in self.procs]

#
# Template emitting code
#

class TemplateManager:
    var_pattern = None
    
    def __init__(self):
        self.variables_by_name = {}
        self.variables_by_values = {}
        self.var_counter = 0

    def get_code_for_values(self, values, varname=None):        
        return self.get_variable_code(
            self.add_variable(values, varname))

    def add_variable(self, values, name=None):
        values = tuple(str(x) for x in values)
        reg_names = self.variables_by_values.setdefault(values, [])
        if name is None:
            if len(reg_names) > 0:
                name = reg_names[0]
            else:
                self.var_counter += 1
                name = 'sub%d' % self.var_counter
        if name not in reg_names:
            reg_names.append(name)
        self.variables_by_name[name] = values
        return name

    def get_variable_code(self, name):
        return self.var_pattern % name


class TempitaManager(TemplateManager):
    var_pattern = '{{%s}}'
    
    def put_start_loop(self, buf):
        var_by_name = self.variables_by_name
        names = var_by_name.keys()
        names.sort()
        for name in names:
            values = var_by_name[name]
            buf.putln('{{py: %s_values=%r}}' % (name, values))
        if len(var_by_name) == 1:
            buf.putln('{{for %s in %s_values}}' % (names[0], names[0]))
        else:
            buf.putln('{{for %s' % ', '.join(names))
            buf.putln('       in zip(%s)}}' % ', '.join('%s_values' % name
                                                        for name in names))
        

    def put_end_loop(self, buf):
        buf.putln('{{endfor}}')


def create_template_manager(cfg):
    return TempitaManager()
