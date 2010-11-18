#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap.version import get_version
from fwrap import git
import re
from copy import copy

#
# Configuration of configuration options
#
ATTR = object() # single attribute (e.g., git-head)
LIST_ITEM = object() # repeated multiple times to form list (e.g., wraps)

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
    
parse_sha_or_nothing = create_string_parser(r'^[0-9a-f]*$')
parse_version = create_string_parser(r'^\w+$')
parse_filename = create_string_parser(r'^.+$')

configuration_dom = {
    # repeat-flag, parser, default value, child-dom
    'git-head' : (ATTR, parse_sha_or_nothing, '', {}),
    'version' : (ATTR, parse_version, None, {}),
    'wraps' : (LIST_ITEM, parse_filename, None, {
        'sha1' : (ATTR, parse_sha_or_nothing, None, {}),
        # TODO: Exclude and include filters.
        }),
    'f77binding' : (ATTR, parse_bool, False, {})
    }


def add_cmdline_options(add_option):
    # Add configuration options. add_option is a callback,
    # and might either be add_option from optparse or
    # add_argument from argparse.
    add_option('--f77binding', action='store_true',
               help='avoid iso_c_binding and use older f2py-style '
               'wrapping instead')
    add_option('--dummy', action='store_true',
               help='dummy development configuration option')
    

def _document_from_cmdline_options(options):
    return {
        'f77binding' : options.f77binding
         }

#
# Main Configuration class, backed by serializable document structure
#

class Configuration:
    # In preferred order when serializing:
    keys = ['version', 'git-head', 'wraps', 'f77binding']

    def __init__(self, document=None, cmdline_options=None):
        if document is None:
            document = apply_dom([])
        if cmdline_options is not None:
            document.update(_document_from_cmdline_options(cmdline_options))

        assert set(self.keys) == set(document.keys())

        # Most options are looked up in document via __getattr__
        self.document = document

        # Non-persistent aliases -- useful if we in the future *may*
        # split one option into more options
        self.fc_wrapper_orig_types = self.f77binding

        # Write-protect ourself
        self.__setattr__ = self._setattr

    def __getattr__(self, attrname):
        return self.document[attrname.replace('_', '-')]

    def _setattr(self, attrname, value):
        raise NotImplementedError()

    def __nonzero__(self):
        # sometimes, during refactoring, ctx appears where a bool
        # did originally
        1/0

    #
    # User-facing methods
    #
    def update(self):
        """
        Updates information that can be acquired from the environment
        """
        self.document['version'] = get_version()
        self.document['git-head'] = git.cwd_rev()

    def serialize_to_pyx(self, buf):
        parse_tree = document_to_parse_tree(self.document, self.keys)
        serialize_inline_configuration(parse_tree, buf)



#
# Configuration section parsing etc.
#
# See tests/test_configuration for examples.
# First, a very simple indentation-based key-value format is parsed into
# a dictionary, and then one can validate the acquired dictionary with
# a DOM
#

#
# Validation and turn raw parse tree into more friendly typed tree
#


class ValidationError(ValueError):
    pass
class ParseError(ValueError):
    pass

def apply_dom(tree, dom=configuration_dom):
    encountered = set()
    result = {}
    # Parse tree and give it meaning according to DOM
    for key, value, children in tree:
        if key not in dom.keys():
            raise ValidationError('Unknown fwrap configuration key: %s' % key)
        nodetype, value_parser, default, child_dom = dom[key]
        try:
            typed_value = value_parser(value)
        except ValueError:
            raise ValidationError('Illegal value for %s: %s' % (key, value))
        if nodetype == ATTR:
            if key in encountered or len(children) > 0:
                raise ValidationError('"%s" should only have one entry without children' % key)
            result[key] = typed_value
        elif nodetype == LIST_ITEM:
            lst = result.get(key, None)
            if lst is None:
                lst = result[key] = []

            children_typed_tree = apply_dom(children, child_dom)
            lst.append((value, children_typed_tree))
        else:
            assert False
        encountered.add(key)
            
    # Fill in defaults
    for key in set(dom.keys()) - encountered:
        nodetype, value_parser, default, child_dom = dom[key]
        if nodetype == ATTR:
            result[key] = default
        elif nodetype == LIST_ITEM:
            assert default is None
            result[key] = []
        else:
            assert False
    return result


#TODO: ordered_keys must be on many levels, traverse DOM structure
#      instead
def document_to_parse_tree(doc, ordered_keys):
    assert set(doc.keys()) == set(ordered_keys)
    result = []
    for key in ordered_keys:
        entry = doc[key]
        if isinstance(entry, list):
            for value, attrs in entry:
                subtree = document_to_parse_tree(attrs, attrs.keys())
                result.append((key, value, subtree))
        else:
            if entry is None:
                value = ''
            else:
                value = str(entry)
            result.append((key, value, []))
    return result

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
            children = []
            result.append((key, value, children))
            # Recurse to capture any children and get next line
            # -- can raise StopIteration
            indent, line_match = _parse_node(it, indent, children)
            

def parse_inline_configuration(s):
    result = []
    it = fwrap_section_re.finditer(s)
    try:
        _parse_node(it, -1, result)
    except StopIteration:
        pass
    return result

INDENT_STR = '    '

def serialize_inline_configuration(parse_tree, buf, indent=0):
    for key, value, children in parse_tree:
        buf.write('#fwrap: %s%s %s\n' % (INDENT_STR * indent, key, value))
        serialize_inline_configuration(children, buf, indent + 1)        

#
# Global vars
#
default_cfg = Configuration()
default_cfg.update()
