#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap.version import get_version
import re

#
# Configuration context for fwrap
#

class Configuration:
    keys = ['version', 'f77binding']
    
    def __init__(self, **kw):
        for key in self.keys:
            if key in kw.keys():
                setattr(self, key, kw[key])
        # Aliases -- useful if we in the future *may*
        # split one option into more options
        self.fc_wrapper_orig_types = self.f77binding
        # Auto-detected variables
        self.version = get_version()        

    def serialize(self):
        # Preserves preferred order of keys
        return [(key, getattr(self, key))
                for key in self.keys]

    def to_dict(self):
        return dict(self.to_list)
    
    def __nonzero__(self):
        1/0

default_cfg = Configuration(f77binding=False)

def add_cmdline_options(add_option):
    # Add configuration options. add_option is a callback,
    # and might either be add_option from optparse or
    # add_argument from argparse.
    add_option('--f77binding', action='store_true',
               help='avoid iso_c_binding and use older f2py-style '
               'wrapping instead')
    add_option('--dummy', action='store_true',
               help='dummy development configuration option')
    

def configuration_from_cmdline(options):
    return Configuration(f77binding=options.f77binding)


#
# Configuration section parsing etc.
#
# See tests/test_configuration for examples.
# First, a very simple indentation-based key-value format is parsed into
# a dictionary, and then one can validate the acquired dictionary with
# a DOM
#
# TODO: Switch to ordered list instead of unordered dict for keys
#
class ValidationError(ValueError):
    pass
class ParseError(ValueError):
    pass

class Node:
    def __init__(self, value='', children=None):
        if children is None:
            children = {}
        if not isinstance(children, dict):
            raise ValueError('children field must be dict')
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

def create_string_parser(regex):
    regex_obj = re.compile(regex)
    def parse(value):
        if regex_obj.match(value) is None:
            raise ValueError()
        return value
    return parse

def parse_bool(value):
    if value == 'True':
        return True
    elif value == 'False':
        return False
    else:
        raise ValueError()
    
parse_sha = create_string_parser(r'[0-9a-f]+')
parse_version = create_string_parser(r'\w+')
parse_filename = create_string_parser(r'.+')

configuration_dom = {
    # repeat-flag, parser, default value, child-dom
    'git-head' : (ONE, parse_sha, None, {}),
    'version' : (ONE, parse_version, None, {}),
    'wraps' : (MANY, parse_filename, None, {
        'sha1' : (ONE, parse_sha, None, {}),
        # TODO: Exclude and include filters.
        }),
    'f77binding' : (ONE, parse_bool, False, {})
    }


def apply_dom(tree, dom=configuration_dom, validate_only=False):
    for key, entries in tree.iteritems():
        if key not in dom.keys():
            raise ValidationError('Unknown fwrap configuration key: %s' % key)
        nentries, value_parser, default, child_dom = dom[key]
        if nentries == ONE and len(entries) != 1:
            raise ValidationError('"%s" should only have one entry' % key)
        for node in entries:
            try:
                value = value_parser(node.value)
            except ValueError:
                raise ValidationError('Illegal value for %s: %s' % (key, node.value))
            if not validate_only:
                node.value = value
            apply_dom(node.children, child_dom)
    if not validate_only:
        # Fill in defaults
        for key in set(dom.keys()) - set(tree.keys()):
            nentries, value_parser, default, child_dom = dom[key]
            if nentries == ONE:
                tree[key] = [Node(default)]
            else:
                assert default is None
                tree[key] = {}

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

#
# Serializing
#
INDENT_STR = '    '

def _serialize_entries(entries, buf, indent=0):
    for key, value in entries:
        if isinstance(value, Node):
            children = value.children
            value = value.value
        else:
            children = None
        if value in ('', None):
            buf.write('#fwrap: %s%s\n' % (INDENT_STR * indent, key))
        else:
            buf.write('#fwrap: %s%s %s\n' % (INDENT_STR * indent, key, value))
        if children is not None:
            _serialize_entries(node.children.iteritems(), buf, indent + 1)

def serialize_configuration_to_pyx(cfg, buf):
    entries = cfg.serialize()
    _serialize_entries(entries, buf)
        
