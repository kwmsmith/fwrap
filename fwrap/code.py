#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from cStringIO import StringIO
from math import ceil, floor
from textwrap import dedent

INDENT = "  "
LINE_LENGTH = 77 # leave room for two '&' characters
BREAK_CHARS = (' ', '\t', ',', '!')
COMMENT_CHAR = '!'

def reflow_fort(code, level=0, max_len=LINE_LENGTH):
    newcode = ['\n'.join(reflow_line(line)) for line in code.splitlines()]
    return '\n'.join(newcode)

def reflow_line(text, level=0, max_len=LINE_LENGTH):
    if text == '':
        return ['']
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

#
# Fortran 77 fixed form
#

def fixed_width_split(input, linelen):
    lines = []
    while len(input) > 0:
        lines.append(input[:linelen])
        input = input[linelen:]
    return lines

class CodeBufferFixedForm(CodeBuffer):
    #
    # Column:
    # 1..5  labels or C
    # 6     blank or continuation character
    # 7-72  code
    # 73-80 unused
    #
    # Variable names are NOT limited to 6 characters.
    # If that is needed, an idea is to auto-mangle all
    # tokens (except for the subroutine/function name).
    
    def __init__(self):
        super(CodeBufferFixedForm, self).__init__(0, '  ')

    def putln(self, input):
        input = self.indent_tok * self._level + input.rstrip()
        lines = fixed_width_split(input, 72 - 6)
        self.sio.write('      %s\n' % lines[0])
        for line in lines[1:]:
            self.sio.write('     &%s\n' % line)


#
# CodeSnippet and related code
#

def as_code_snippet(x):
    pass

def _format(s, *args, **kw):
    if len(args) > 0 and len(kw) > 0:
        raise ValueError('Only args or kwargs allowed')
    if len(args) > 0:
        return s % args
    elif len(kw) > 0:
        return s % kw
    else:
        return s

class CodeSnippet(object):
    def __init__(self, provides, requires, code=None, *args, **kw):
        self.provides = provides
        if isinstance(requires, basestring):
            raise ValueError('requires must be an iterable or set')
        self.requires = frozenset(requires)
        self.lines = []
        if code is None:
            pass
        elif isinstance(code, basestring):
            self.put(code, *args, **kw)
        elif isinstance(code, list):
            self.lines.extend(code)
        else:
            raise TypeError('code argument')

    def putln(self, line, *args, **kw):
        self.lines.append(_format(line, *args, **kw))

    def put(self, block, *args, **kw):
        block = dedent(block)
        block = _format(block, *args, **kw)
        self.lines.extend(block.split('\n'))

    def __eq__(self, other):
        if self is other:
            return True
        return (type(self) == type(other) and
                self.provides == other.provides and
                self.requires == other.requires and
                self.lines == other.lines)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<CodeSnippet provides=%r requires=%r lines=%r>' % (
            self.provides, self.requires, '\n'.join(self.lines))


def merge_code_snippets(snippets):
    """
    ``snippets`` is a list of CodeSnippet instances, where it is
    allowed that multiple code snippets has the same ``provides``
    identifier. Any snippets with the same idenfifier are merged
    into a single CodeSnippet instance and inserted in the location
    of the first participating CodeSnippet (the other ones being
    removed).
    """
    by_requires = {}
    for s in snippets:
        by_requires.setdefault(s.provides, []).append(s)
    result = []
    for s in snippets:
        group = by_requires.get(s.provides)
        if group is not None:
            merged = CodeSnippet(provides=s.provides,
                                 requires=frozenset.union(*[t.requires for t in group]),
                                 code=sum([t.lines for t in group], []))
            result.append(merged)
            del by_requires[s.provides]
    return result

def emit_code_snippets(snippets, buf=None):
    """
    Emits the contents of the DAG described by ``snippets`` (a list of
    CodeSnippet instances) to buf, in such a way that all requirements
    are satisfied (a topological ordering). The sorting is stable; the
    sense that order of the nodes given in the ``snippets`` list is
    used when the order would otherwise be arbitrary. See also
    ``merge_code_snippets``, which is performed initially.
    """
    if buf is None:
        buf = CodeBuffer()
    snippets = merge_code_snippets(snippets)
    snippets = topological_sort(snippets)
    for snippet in snippets:
        buf.putlines(snippet.lines)
    return buf

# Algorithm
#
# Interface: Each node should have a unique provides attributes (a comparable
# identifier) and a requires attribute (a frozenset of identifiers)
class DependencyException(Exception):
    pass

def topological_sort(input_nodes):
    result = []
    been_visited = set()

    def visit(node):
        if node.provides not in been_visited:
            been_visited.add(node.provides)
            # Visit the requirements in the order given in the
            # original input array (stable ordering).  This increases
            # complexity, but we will only use this code for tens of
            # nodes and readability is more important than coming up
            # with something more clever.
            requires = set(node.requires)
            for y in input_nodes:
                if y.provides in requires:
                    requires.remove(y.provides)
                    visit(y)
            if len(requires) != 0:
                raise DependencyException('Node(s) not present: %s' % ', '.join(
                    repr(x) for x in requires))
            result.append(node)
            

    leafs = find_leafs(input_nodes)
    for leaf in leafs:
        visit(leaf)
        
    return result


def find_leafs(nodes):
    required = set()
    for node in nodes:
        required |= node.requires
    return [node for node in nodes
            if node.provides not in required]
    
