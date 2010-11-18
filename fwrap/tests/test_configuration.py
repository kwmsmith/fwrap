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
from fwrap.configuration import *

def test_parser():
    code = dedent("""
    Not included
    foo
    #fwrap: wraps source_a.f90    
    #fwrap:     sha1 346e
    #fwrap: git-head 1872
    bar
    #fwrap: wraps source_a.f90
    #fwrap: has-no-value
    yey!
    """)

    obj = parse_inline_configuration(code)
    eq_(obj, {'git-head': [Node('1872')],
              'wraps': [Node('source_a.f90',
                         {'sha1': [Node('346e')]}),
                        Node('source_a.f90')],
              'has-no-value': [Node()]})

    assert_raises(ValueError, parse_inline_configuration,
                  "#fwrap:git-head 342d") # need leading space
    assert_raises(ValueError, parse_inline_configuration,
                  dedent("""
                  #fwrap: foo value
                  #fwrap:     child1
                  #fwrap:    child2
                  """)) # inconsistent indentation


def test_apply_dom():
    tree = {'git-head': [Node('1872')],
            'wraps': [Node('source_a.f90',
                       {'sha1': [Node('346e')]}),
                      Node('source_a.f90')]}
    try:
        apply_dom(tree)
    except ValidationError:
        assert_true(False)

    ok_('f77binding' in tree.keys())
    eq_(tree['f77binding'][0].value, False)

    tree['wraps'][0].children['sha1'][0].value = 'not-a-sha'
    assert_raises(ValidationError, apply_dom, tree)

    assert_raises(ValidationError, apply_dom,
                  {'unknown' : [Node(),]})
    assert_raises(ValidationError, apply_dom,
                  {'git-head' : [Node('1'),Node('1'),]}) # ONE only


    tree = {'f77binding' : [Node('True')]}
    apply_dom(tree, validate_only=True)
    eq_(type(tree['f77binding'][0].value),  str)
    apply_dom(tree, validate_only=False)
    ok_(type(tree['f77binding'][0].value), bool)
