#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from cStringIO import StringIO
from math import ceil, floor

INDENT = "  "
LINE_LENGTH = 77 # leave room for two '&' characters
BREAK_CHARS = (' ', '\t', ',', '!')
COMMENT_CHAR = '!'

def reflow_fort(code, level=0, max_len=LINE_LENGTH):
    newcode = ['\n'.join(reflow_line(line)) for line in code.splitlines()]
    return '\n'.join(newcode)

def reflow_line(text, level=0, max_len=LINE_LENGTH):
    line_len = max_len - len(INDENT)*level
    broken_text = []
    lim = int(ceil(len(text)/float(line_len)))
    for i in range(lim):
        broken_text.append('&'+text[i*line_len:(i+1)*line_len]+'&')

    # strip off the beginning & ending continuations.
    broken_text[0] = broken_text[0][1:]
    broken_text[-1] = broken_text[-1][:-1]

    # prepend the indent
    broken_text = [INDENT*level + txt for txt in broken_text]

    return broken_text

def _break_line(line, level, max_len):

    line = INDENT*level+line

    if len(line) <= max_len:
        # return line
        return [line]

    # break up line.
    in_comment = False
    in_string = False
    in_escape = False
    last_break_pos = -1
    for idx, ch in enumerate(line):
        if idx+1 > max_len:
            if last_break_pos < 0:
                raise RuntimeError("line too long and unable to break it up.")
            return [line[:last_break_pos]] + \
                        break_line(line[last_break_pos:], level, max_len)

        if ch in BREAK_CHARS and not in_comment and not in_string:
            last_break_pos = idx

        if ch == COMMENT_CHAR and not in_comment and not in_string:
            in_comment = True
        elif ch in ('"', "'") and not in_string and not in_comment:
            in_string = True
        elif (ch in ('"', "'") and in_string and not
                    in_escape and not in_comment):
            in_string = False

        if ch == '\\' and not in_escape:
            in_escape = True
        elif in_escape:
            in_escape = False

class CodeBuffer(object):
    def __init__(self, level=0, indent="    "):
        self.sio = StringIO()
        self._level = level
        self.indent_tok = indent

    def putempty(self):
        self.sio.write('\n')

    def putlines(self, lines):
        if isinstance(lines, basestring):
            lines = lines.splitlines()
        for line in lines:
            self.putln(line)

    def putline(self, line):
        self.putln(line)

    def putln(self, line):
        line = line.rstrip()
        if line:
            self.sio.write(self.indent_tok * self._level + line + '\n')
        else:
            self.putempty()

    def putblock(self, block):
        self.sio.write(block)

    def indent(self):
        self._level += 1

    def dedent(self):
        self._level -= 1

    def getvalue(self):
        return self.sio.getvalue()

    def write(self, s):
        self.sio.write(s)
