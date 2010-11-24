#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import code

from nose.tools import (ok_, eq_, set_trace, raises, assert_raises,
                        assert_false, assert_true)
import sys
from pprint import pprint
from textwrap import dedent
from StringIO import StringIO

from fwrap.deduplicator import *

def assert_unordered_list_eq(lst_a, lst_b):
    eq_(len(lst_a), len(lst_b))
    for item in lst_a:
        count_in_a = sum(item == x for x in lst_a)
        count_in_b = sum(item == x for x in lst_b)
        eq_(count_in_a, count_in_b)

def test_grouping():
    eq_(find_candidate_groups_by_name([]), [])

    assert_unordered_list_eq(find_candidate_groups_by_name(
        ['sbar', 'foo', 'dbar', 'baz', 'cbar', 'solid', 'comp',
         'sfoo', 'zfoo', 'cfoo']),
                             [['sbar', 'dbar', 'cbar'],
                              ['sfoo', 'cfoo', 'zfoo']])

def test_tempita():
    mgr = TempitaManager()
    mgr.add_variable([1, 2, 3], 'myname')
    eq_(mgr.get_variable_code('myname'), '{{myname}}')
    eq_(mgr.add_variable([1, 2, 3]), 'myname')
    eq_(mgr.add_variable([1, 5, 3]), 'sub1')
    eq_(mgr.add_variable([1, 3, 3]), 'sub2')
    eq_(mgr.add_variable([1, 5, 3]), 'sub1')

    

