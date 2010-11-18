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


def test_validation():
    tree = {'git-head': [Node('1872')],
            'wraps': [Node('source_a.f90',
                       {'sha1': [Node('346e')]}),
                      Node('source_a.f90')]}
    try:
        validate_configuration(tree)
    except ValidationError:
        assert_true(False)

    tree['wraps'][0].children['sha1'][0].value = 'not-a-sha'
    assert_raises(ValidationError, validate_configuration, tree)

    assert_raises(ValidationError, validate_configuration,
                  {'unknown' : [Node(),]})
    assert_raises(ValidationError, validate_configuration,
                  {'git-head' : [Node('1'),Node('1'),]}) # ONE only

    
