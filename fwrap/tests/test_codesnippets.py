#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap import cy_wrap
from fwrap import pyf_iface as pyf
from fwrap import fc_wrap
from fwrap.code import *
from pprint import pprint
from textwrap import dedent

from nose.tools import ok_, eq_, set_trace

def test_merge():
    # Build a DAG
    nodes = []
    def node(provides, requires):
        nodes.append(CodeSnippet(provides, requires, [str(len(nodes))]))

    node('A', [])
    node('B', [])
    node('C', [])
    node('A', ['B'])
    node('A', [])
    node('C', [])
    nodes = merge_code_snippets(nodes)
    pprint(nodes)
    eq_(len(nodes), 3)
    eq_(nodes[0], CodeSnippet('A', ['B'], ['0', '3', '4']))
    eq_(nodes[1], CodeSnippet('B', [], ['1']))
    eq_(nodes[2], CodeSnippet('C', [], ['2', '5']))
    
    should_be_idempotent = merge_code_snippets(nodes)
    eq_(should_be_idempotent, nodes)
    ok_(should_be_idempotent is not nodes)

def test_basic():
    # Build a DAG
    nodes = []
    def node(provides, requires):
        cs = CodeSnippet(provides, requires)
        if requires:
            cs.putln('Put on %s (requires %s)' % (provides, ', '.join(requires)))
        else:
            cs.putln('Put on %s' % provides)
        nodes.append(cs)

    node('space suit', ['sweater'])
    node('socks', [])
    node('pants', ['underwear'])
    node('t-shirt', [])
    node('sweater', ['t-shirt'])
    node('underwear', [])
    node('space suit', ['pants'])

    # Serialize it
    buf = emit_code_snippets(nodes)
    eq_(buf.getvalue(), dedent('''\
        Put on underwear
        Put on pants (requires underwear)
        Put on t-shirt
        Put on sweater (requires t-shirt)
        Put on space suit (requires sweater)
        Put on space suit (requires pants)
        Put on socks
        '''))
    
    # Try with another order; move the initial (space suit->sweater) last
    nodes.append(nodes[0])
    del nodes[0]
    
    buf = emit_code_snippets(nodes)
    eq_(buf.getvalue(), dedent('''\
        Put on socks
        Put on underwear
        Put on pants (requires underwear)
        Put on t-shirt
        Put on sweater (requires t-shirt)
        Put on space suit (requires pants)
        Put on space suit (requires sweater)
        '''))

    
    
    

