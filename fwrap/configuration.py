import re

def add_configure_options(add_option):
    # Add configuration options. add_option is a callback,
    # and might either be add_option from optparse or
    # add_argument from argparse.

    # This is just a place-holder until merged with f77 branch.
    add_option('--dummy', action='store_true',
               help='dummy development configuration option')
    


#
# Configuration section parsing etc.
#
# See tests/test_configuration for examples.
# First, a very simple indentation-based key-value format is parsed into
# a dictionary, and then one can validate the acquired dictionary with
# a DOM
#
class ValidationError(ValueError):
    pass
class ParseError(ValueError):
    pass

class Node:
    def __init__(self, value='', children=None):
        if children is None:
            children = {}
        if not isinstance(value, str):
            raise ValueError('value field must be str')
        if not isinstance(children, dict):
            raise ValueError('children field must be str')
        self.value = value
        self.children = children
    def __eq__(self, other):
        return (isinstance(other, Node) and
                other.value == self.value and
                other.children == self.children)
    def __repr__(self):
        #buf = StringIO()
        #child_repr = pprint(self.children, buf)
        return 'Node(value=%r, children=%r)' % (self.value, self.children)

#
# Validation
#
ONE, MANY = object(), object()

sha_re = re.compile(r'[0-9a-f]+')
version_re = re.compile(r'\w+')
filename_re = re.compile('.*')

configuration_dom = {
    'git-head' : (ONE, sha_re, {}),
    'version' : (ONE, version_re, {}),
    'wraps' : (MANY, filename_re, {
        'sha1' : (ONE, sha_re, {}),
        # TODO: Exclude and include filters.
        }),
    }


def validate_configuration(tree, dom=configuration_dom):
    for key, entries in tree.iteritems():
        if key not in dom.keys():
            raise ValidationError('Unknown fwrap configuration key: %s' % key)
        nentries, value_re, child_dom = dom[key]
        if nentries == ONE and len(entries) != 1:
            raise ValidationError('"%s" should only have one entry' % key)
        for node in entries:
            if value_re.match(node.value) is None:
                raise ValidationError('Illegal value for %s: %s' % (key, node.value))
            validate_configuration(node.children, child_dom)


#
# Parsing
#
fwrap_section_re = re.compile(r'^#fwrap:(.+)$', re.MULTILINE)
config_line_re = re.compile(r' (\s*)([\w-]+)(.*)$')

def _parse_node(it, parent_indent, result):
    # Parses the children of the current node (possibly root),
    # defined as having indent larger than parent_indent, and puts
    # contents into result dictionary. Returns the line
    # not parsed (because it has less indent).

    line = it.next().group(1)
    line_match = config_line_re.match(line)
    if line_match is None:
        raise ParseError('Can not parse fwrap config line: %s' % line)
    indent = len(line_match.group(1))
    cur_indent = None
    while True: # exits by StopIteration
        if indent <= parent_indent:
            return indent, line_match
        else:
            if cur_indent is None:
                cur_indent = indent
            elif indent !=  cur_indent:
                raise ParseError('Inconsistent indentation in fwrap config')
            key = line_match.group(2)
            value = line_match.group(3).strip()
            # Create children dict, and insert it and the value in parent's
            # result dictionary
            children = {}
            lst = result.get(key, None)
            if lst is None:
                lst = result[key] = []
            lst.append(Node(value=value, children=children))
            # Recurse to capture any children and get next line
            # -- can raise StopIteration
            indent, line_match = _parse_node(it, indent, children)
            

def parse_inline_configuration(s):
    result = {}
    it = fwrap_section_re.finditer(s)
    try:
        _parse_node(it, -1, result)
    except StopIteration:
        pass
    return result
