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

from nose.tools import eq_

def remove_common_indent(s):
    if not s:
        return s
    lines_ = s.splitlines()

    # remove spaces from ws lines
    lines = []
    for line in lines_:
        if line.rstrip():
            lines.append(line.rstrip())
        else:
            lines.append("")

    fst_line = None
    for line in lines:
        if line:
            fst_line = line
            break

    ws_count = 0
    for ch in fst_line:
        if ch == ' ':
            ws_count += 1
        else:
            break

    if not ws_count: return s

    ret = []
    for line in lines:
        line = line.rstrip()
        if line:
            assert line.startswith(' '*ws_count)
            ret.append(line[ws_count:])
        else:
            ret.append('')
    return '\n'.join(ret)

def compare(s1, s2):
    ss1 = remove_common_indent(s1.rstrip())
    ss2 = remove_common_indent(s2.rstrip())
    for idx, lines in enumerate(zip(ss1.splitlines(), ss2.splitlines())):
        L1, L2 = lines
        assert L1 == L2, "\n%s\n != \n%s\nat line %d: '%s' != '%s'" % (ss1, ss2, idx, L1, L2)
