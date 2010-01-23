from fwrap_src import code

from nose.tools import ok_, eq_, set_trace

import sys
from pprint import pprint

# 1) Any non-comment line can be broken anywhere -- in the middle of words,
#    etc.
# 2) Comments are stripped out of the source and are to be ignored in reflowing
#    text.

def test_breakup():
    line = """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"""
    
    for chunk in (1, 2, 3, 5, 10, 20, 50, len(line)):
        yield breakup_gen, line, chunk

def breakup_gen(line, chunk):
    ret = code.reflow(line, 0, chunk)
    eq_(simple_break(line, chunk), ret)
    for part in ret[1:-1]:
        eq_(len(part), chunk+2)
    if len(ret) == 1:
        eq_(len(ret[0]), len(line))
    else:
        eq_(len(ret[0]), chunk+1)
        ok_(len(ret[-1]) <= chunk+1)
    orig = ''.join(ret)
    orig = orig.replace('&', '')
    eq_(orig, line)

def simple_break(text, chunk):
    i = 0
    test_ret = []
    while True:
        test_ret.append('&'+text[i*chunk:(i+1)*chunk]+'&')
        if (i+1)*chunk >= len(text):
            break
        i += 1

    test_ret[0] = test_ret[0][1:]
    test_ret[-1] = test_ret[-1][:-1]
    # set_trace()
    return test_ret

def test_nobreak():
    line = """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"""
    ret = code.reflow(line, 0, 100)
    eq_(ret, [line])

def test_indent():
    line = "12345678901234567890"
    ret = code.reflow(line, 1, 100)
    eq_(ret, [code.INDENT+line])
    ret = code.reflow(line, 1, 10)
    eq_(ret, [code.INDENT+line[:8]+'&', code.INDENT+'&'+line[8:16]+'&', code.INDENT+'&'+line[16:]])
    set_trace()
