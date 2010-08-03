#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Fwrap project nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
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

    def indent(self):
        self._level += 1

    def dedent(self):
        self._level -= 1

    def getvalue(self):
        return self.sio.getvalue()

    def write(self, s):
        self.sio.write(s)
