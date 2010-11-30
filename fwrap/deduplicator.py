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
    name_to_proc = dict((proc.name, proc) for proc in cy_ast)
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
        cy_ast = [(template_node if node.name == to_sub else node)
                  for node in cy_ast
                  if node.name not in to_remove]
    return cy_ast

def cy_create_template(procs, cfg):
    """Make an attempt to merge the given procedures into a template
    """

    template_mgr = create_template_manager(cfg)
    merged_attrs = merge_node_attributes(procs, template_mgr,
                                         exclude=('in_args', 'out_args', 'call_args',
                                                  'all_dtypes_list'))

    in_args = cy_merge_args([proc.in_args for proc in procs], template_mgr)
    out_args = cy_merge_args([proc.out_args for proc in procs], template_mgr)
    call_args = cy_merge_args([proc.call_args for proc in procs], template_mgr)
    
    return TemplatedProcedure(template_mgr=template_mgr,
                              in_args=in_args,
                              out_args=out_args,
                              call_args=call_args,
                              all_dtypes_list=sum([proc.all_dtypes() for proc in procs], []),
                              names=[proc.cy_name for proc in procs],
                              **merged_attrs)

def cy_merge_args(arg_lists, template_mgr):
    if not all_equal(len(lst) for lst in arg_lists):
        raise UnableToMergeError()
    for matched_args in zip(*arg_lists):
        arg0 = matched_args[0]
        for arg in matched_args[1:]:
            if not arg0.equal_up_to_type(arg):
                raise UnableToMergeError()

    merged_args = [get_templated_cy_arg(matched_args,
                                        template_mgr)
                   for matched_args in zip(*arg_lists)]
    return merged_args

def get_templated_cy_arg(args, template_mgr):
    cls = type(args[0])
    extra = ()
    if cls == cy_wrap._CyArrayArg:
        cls = TemplatedCyArrayArg
        extra = ('npy_enum',)
    elif cls in (cy_wrap._CyArg, cy_wrap._CyCmplxArg):
        cls = TemplatedCyArg
    elif cls == cy_wrap._CyErrStrArg:
        cls = cy_wrap._CyErrStrArg
    else:
        warn('Not implemented: Template merging of arguments of type %s' % cls.__name__)
        raise UnableToMergeError()
    
    attrs = merge_node_attributes(args, template_mgr,
                                  exclude=('dtype',),
                                  extra=extra)
    return cls(template_mgr=template_mgr,
               dtype=None,
               **attrs) 

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

def merge_node_attributes(nodes, template_mgr,
                          exclude=(), extra=()):
    assert all_equal(set(node.attributes) for node in nodes)
    attributes = nodes[0].attributes

    attrs = {}
    for attrname in attributes + extra:
        if attrname in exclude:
            continue
        values = [getattr(node, attrname) for node in nodes]
        if all_equal(values):
            attrs[attrname] = values[0]
        else:
            if not all(isinstance(value, str) for value in values):
                raise ValueError('Cannot merge non-string attribute: %s' % attrname)
            code = template_mgr.get_code_for_values(values, attrname)
            attrs[attrname] = code
    return attrs

class TemplatedCyArrayArg(cy_wrap._CyArrayArg):

    pass
#    def _update(self):
#        pass
##     merge_attr_names = ['intern_name', 'extern_name',
##                         'ktp', 'py_type_name', 'npy_enum']
##     def __init__(self, args, template_mgr):
##         cy_wrap._CyArrayArg.__init__(self, args[0].arg)
##         merge_attributes_inplace(self, args, self.merge_attr_names, template_mgr)

class TemplatedCyArg(cy_wrap._CyArg):
    pass
#    mandatory = cy_wrap._CyArg.mandatory + ('cy_dtype_name',)
#    def _update(self):
#        pass
#    merge_attr_names = ['intern_name', 'name', 'cy_dtype_name']
##     def __init__(self, args, template_mgr):
##         cy_wrap._CyArg.__init__(self, args[0].arg)
##         merge_attributes_inplace(self, args, self.merge_attr_names, template_mgr)

class TemplatedProcedure(cy_wrap.CyProcedure):
    mandatory = cy_wrap.CyProcedure.mandatory + ('template_mgr', 'names')

    def _update(self):
        super(TemplatedProcedure, self)._update()

    def generate_wrapper(self, ctx, buf):
        self.template_mgr.put_start_loop(buf)
        cy_wrap.CyProcedure.generate_wrapper(self, ctx, buf)
        self.template_mgr.put_end_loop(buf)

    def get_names(self):
        return self.names

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
