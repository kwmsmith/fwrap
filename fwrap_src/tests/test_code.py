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
    ret = code.reflow_line(line, 0, chunk)
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
    ret = code.reflow_line(line, 0, 100)
    eq_(ret, [line])

def test_indent():
    line = "12345678901234567890"
    ret = code.reflow_line(line, 1, 100)
    eq_(ret, [code.INDENT+line])
    ret = code.reflow_line(line, 1, 10)
    eq_(ret, [code.INDENT+line[:8]+'&', code.INDENT+'&'+line[8:16]+'&', code.INDENT+'&'+line[16:]])
    # set_trace()

def test_reflow():
    reflow_src = ("subroutine many_args(a0, a1, a2, a3, a4, a5, a6, a7, a8, ",
                  "a9, a20, a21, a22, a23, a24, a25, a26, a27, a28, a29, a30",
                  ", a31, a32, a33, a34, a35, a36, a37, a38, a39, a40, a41, ",
                  "a42, a43, a44, a45, a46, a47, a48, a49)\n",
                  "    implicit none\n",
                  "    integer, intent(in) :: a0, a1, a2, a3, a4, a5, a6, ",
                  "a7, a8, a9, a20, a21, a22, a23, a24, a25, a26, a27, a28, ",
                  "a29, a30, a31, a32, a33, a34, a35, a36, a37, a38, a39, ",
                  "a40, a41, a42, a43, a44, a45, a46, a47, a48, a49\n",
                  "end subroutine many_args")
    
    buf = CodeBuffer()
    buf.putline(reflow_fort(reflow_src))
    for line in buf.getvalue().splitlines():
        ok_(len(line) <= 79, "len('%s') > 79" % line)

            
    