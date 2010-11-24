#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

#
# Currently only deduplicates contents of Cython pyx files
#

import re
from fwrap import cy_wrap
from warnings import warn

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
    name_to_proc = dict((proc.unmangled_name, proc) for proc in cy_ast)
    procnames = name_to_proc.keys()
    groups = find_candidate_groups_by_name(procnames)
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
        cy_ast = [(template_node if node.unmangled_name == to_sub else node)
                  for node in cy_ast
                  if node.unmangled_name not in to_remove]
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

def merge_attributes(target_obj, source_objs, attribute_names,
                     template_mgr):
    for merge_attr in attribute_names:
        values = [getattr(obj, merge_attr) for obj in source_objs]
        if all_equal(values):
            setattr(target_obj, merge_attr, values[0])
        else:
            code = template_mgr.get_code_for_values(values, merge_attr)
            setattr(target_obj, merge_attr, code)

class TemplatedCyArrayArg(cy_wrap._CyArrayArgWrapper):
    merge_attr_names = ['intern_name', 'extern_name',
                        'ktp', 'py_type_name', 'npy_enum']
    def __init__(self, args, template_mgr):
        cy_wrap._CyArrayArgWrapper.__init__(self, args[0].arg)
        merge_attributes(self, args, self.merge_attr_names, template_mgr)

class TemplatedCyArg(cy_wrap._CyArgWrapper):
    merge_attr_names = ['intern_name', 'name', 'cy_dtype_name']
    def __init__(self, args, template_mgr):
        cy_wrap._CyArgWrapper.__init__(self, args[0].arg)
        merge_attributes(self, args, self.merge_attr_names, template_mgr)

def get_templated_cy_arg_wrapper(args, template_mgr):
    cls = type(args[0])
    if cls == cy_wrap._CyArrayArgWrapper:
        return TemplatedCyArrayArg(args, template_mgr)
    elif cls in (cy_wrap._CyArgWrapper, cy_wrap._CyCmplxArg):
        return TemplatedCyArg(args, template_mgr)
    else:
        warn('Not implemented: Template merging of arguments of type %s' % cls.__name__)
        raise UnableToMergeError()

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
        self.values_to_name = {}
        self.name_to_values = {}
        self.prefix_counters = {}

    def get_code_for_values(self, values, prefix='sub'):        
        return self.get_variable_code(
            self.add_variable(values, prefix))

    def add_variable(self, values, prefix='sub'):
        values = tuple(str(x) for x in values)
        name = self.values_to_name.get(values, None)
        if name is None:
            # Count number of times each prefix has been used
            count = self.prefix_counters[prefix] = self.prefix_counters.get(prefix, 0) + 1
            if count == 1:
                name = prefix
            else:
                name = prefix + str(count)
            self.values_to_name[values] = name
            self.name_to_values[name] = values
        return name

    def get_variable_code(self, name):
        return self.var_pattern % name


class TempitaManager(TemplateManager):
    var_pattern = '{{%s}}'
    
    def put_start_loop(self, buf):
        var_by_name = self.name_to_values
        names = var_by_name.keys()
        names.sort()
        buf.putln('{{py:')
        for name in names:
            values = var_by_name[name]
            buf.putln('%s_values = %s' % (name, repr(list(values))))
        buf.putln('}}')
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
