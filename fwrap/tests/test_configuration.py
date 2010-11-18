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
from StringIO import StringIO

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
    eq_(obj, [
        ('wraps', 'source_a.f90', [
            ('sha1', '346e', [])
            ]),
        ('git-head', '1872', []),
        ('wraps', 'source_a.f90', []),
        ('has-no-value', '', [])
        ])
        

    assert_raises(ValueError, parse_inline_configuration,
                  "#fwrap:git-head 342d") # need leading space
    assert_raises(ValueError, parse_inline_configuration,
                  dedent("""
                  #fwrap: foo value
                  #fwrap:     child1
                  #fwrap:    child2
                  """)) # inconsistent indentation


def test_apply_dom():

    def filter_tree(x):
        # Remove top-level keys we don't use in the test
        return dict((key, value)
                    for key, value in x.iteritems()
                    if key in ('git-head', 'wraps', 'f77binding'))
    
    parse_tree = [
        ('git-head', '1872', []),
        ('wraps', 'source_a.f90', [
            ('sha1', '346e', [])
            ]),
        ('wraps', 'source_b.f90', []),
        ]
    try:
        typed_tree = filter_tree(apply_dom(parse_tree))
    except ValidationError:
        ok_(False)

    eq_(typed_tree, {
        'git-head' : '1872',
        'wraps' : [
            ('source_a.f90', {'sha1': '346e'}),
            ('source_b.f90', {'sha1': None})
            ],
        'f77binding' : False
        })

    parse_tree[0] = ('git-head', 'not-a-sha', [])
    assert_raises(ValidationError, apply_dom, parse_tree)

    assert_raises(ValidationError, apply_dom,
                  [('unknown', 'asdf', [])])
    assert_raises(ValidationError, apply_dom,
                  [('git-head', '1', []),
                   ('git-head', '1', [])]) # repetead


def test_serialize():
    key_order = ['git-head', 'wraps', 'f77binding']
    doc = {
        'git-head' : '1872',
        'wraps' : [
            ('source_a.f90', {'sha1': '346e'}),
            ('source_b.f90', {})
            ],
        'f77binding' : False
        }
    parse_tree = document_to_parse_tree(doc, key_order)
    eq_(parse_tree, [
        ('git-head', '1872', []),
        ('wraps', 'source_a.f90', [
            ('sha1', '346e', [])
            ]),
        ('wraps', 'source_b.f90', []),
        ('f77binding', 'False', [])
        ])

    buf = StringIO()
    serialize_inline_configuration(parse_tree, buf)
    eq_(buf.getvalue(), dedent("""\
        #fwrap: git-head 1872
        #fwrap: wraps source_a.f90
        #fwrap:     sha1 346e
        #fwrap: wraps source_b.f90
        #fwrap: f77binding False
        """))

    
