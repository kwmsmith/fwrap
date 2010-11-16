#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

#
# Configuration context for fwrap
#

def update_self_from_args(obj, locals_result):
    del locals_result['self']
    obj.__dict__.update(locals_result)

class Configuration:
    def __init__(self, f77binding, fc_wrapper_orig_types):
        update_self_from_args(self, locals())
    def __nonzero__(self):
        1/0

default_cfg = Configuration(False, False)
