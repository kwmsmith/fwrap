#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

#
# Currently only deduplicates Cython pyx files
#

import re

class UnableToMergeError(Exception):
    pass

def cy_deduplify(cy_ast, cfg):
    name_to_proc = dict((proc.name, proc) for proc in cy_ast)
    procnames = name_to_proc.keys()
    groups = find_candidate_groups_by_name(procnames)

    for names_in_group in groups:
        procs = [name_to_proc[name] for name in names_in_group]
        try:
            template_node = cy_create_template(procs)
        except UnableToMergeError:
            continue
        # Insert the created template at the position
        # of the *first* routine, and remove the other
        # routines
        to_sub = group[0]
        to_remove = group[1:]
        cy_ast = [(template_node if node.name == to_sub else node)
                  for node in cy_ast
                  if node.name not in to_remove]
                  
    return cy_ast

def cy_create_template(procs):
    """Make an attempt to merge the given procedures into a template
    """
    raise UnableToMergeError


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
    
