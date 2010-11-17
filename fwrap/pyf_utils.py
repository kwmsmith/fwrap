#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# Utilities for working with .pyf files
# Mostly just hacks for easier porting from f2py to fwrap

import re

_c_to_cython_dictionary = {
    '&&' : 'and',
    '||' : 'or',
    '!' : 'not',
    # Just to 'convert' whitespace style as well, include
    # other operators
    '<' : '<',
    '<=' : '<=',
    '==' : '==',
    '>=' : '>=',
    '>' : '>',
    '!=' : '!='
}

# Add spaces
for key, value in _c_to_cython_dictionary.iteritems():
    _c_to_cython_dictionary[key] = ' %s ' % value

cast_re = re.compile(r'\((int|float|double)\)([a-zA-Z0-9_]+)')
whitespace_re = re.compile(r'\s\s+')
operators_re = re.compile(r'&&|\|\||<=?|>=?|==|!=?')

def c_to_cython(expr):
    # Deal with the most common cases to reduce the amount
    # of manual modification needed afterwards. This is used
    # in check(...), so support common boolean constructs
    def su(m):
        return _c_to_cython_dictionary[m.group(0)]
    expr = operators_re.sub(su, expr)
    expr = whitespace_re.sub(' ', expr) # Remove redundant spaces introduced
    expr = cast_re.sub(r'<\1>\2', expr) # (int)v -> <int>v
    return expr.strip()

if __name__ == '__main__':
    # TODO: testcase...
    print repr(c_to_cython(' ((int)a>=3) && !(b!=c) || (e<f)'))
