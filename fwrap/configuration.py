#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from fwrap.version import get_version
from fwrap import git
import re
import os
from StringIO import StringIO
from copy import copy, deepcopy

#
# Configuration of configuration options
#
ATTR = object() # single attribute (e.g., git-head)
LIST_ITEM = object() # repeated multiple times to form list (e.g., wraps)
NODE = object()

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
    
configuration_dom = {
    # nodetype, parser/regex, default-value, child-dom
    'vcs' : (NODE, r'none|git', 'none', {
        'head' : (ATTR, r'^[0-9a-f]*$', '', {}),
        }),
    'version' : (ATTR, r'^[0-9.]+(dev_[0-9a-f]+)?$', None, {}),
    'wraps' : (LIST_ITEM, r'^.+$', None, {
        'sha1' : (ATTR, r'^[0-9a-f]*$', None, {}),
        }),
    'exclude' : (LIST_ITEM, r'^[a-zA-Z0-9_]+$', None, {}),
    'f77binding' : (ATTR, parse_bool, False, {}),
    'detect-templates' : (ATTR, parse_bool, False, {}),
    'auxiliary' : (LIST_ITEM, r'^.+$', None, {}),
    }


def add_cmdline_options(add_option):
    # Add configuration options. add_option is a callback,
    # and might either be add_option from optparse or
    # add_argument from argparse.
    add_option('--f77binding', action='store_true',
               help='avoid iso_c_binding and use older f2py-style '
               'wrapping instead')
    add_option('--detect-templates', action='store_true',
               help='detect procs repeated with different types '
               'and output .pyx.in Tempita template instead of .pyx')
    add_option('--dummy', action='store_true',
               help='dummy development configuration option')
    

def _document_from_cmdline_options(options):
    return {
        'f77binding' : options.f77binding,
        'detect-templates' : options.detect_templates,
         }

#
# Main Configuration class, backed by serializable document structure
#

class Configuration:
    # In preferred order when serializing:
    keys = ['version', 'vcs', 'wraps', 'exclude', 'f77binding', 'detect-templates',
            'auxiliary']

    @staticmethod
    def create_from_file(filename):
        with file(filename, 'r') as f:
            contents = f.read()
        parse_tree = parse_inline_configuration(contents)
        document = apply_dom(parse_tree)
        return Configuration(filename, document)

    def __init__(self, pyx_filename, document=None, cmdline_options=None):
        if document is None:
            document = apply_dom([])
        if cmdline_options is not None:
            document.update(_document_from_cmdline_options(cmdline_options))

        assert set(self.keys) == set(document.keys()), (self.keys, document.keys())

        # Most options are looked up in document via __getattr__
        self.document = document
        
        # Name comes from filename and not document
        if pyx_filename is not None: # allow default_cfg
            if not pyx_filename.endswith('.pyx'):
                raise ValueError('need a pyx file')
            path, basename = os.path.split(pyx_filename)
            self.wrapper_name = basename[:-4]
            self.wrapper_path = os.path.realpath(path)

        # Non-persistent aliases -- useful if we in the future *may*
        # split one option into more options
        self.fc_wrapper_orig_types = self.f77binding

        # Write-protect ourself
        self.__setattr__ = self._setattr

    def _setattr(self, attrname, value):
        raise NotImplementedError()

    def __nonzero__(self):
        # sometimes, during refactoring, ctx appears where a bool
        # did originally
        1/0

    def __getattr__(self, attrname):
        if attrname.startswith('_'):
            raise AttributeError("has no attribute '%s'" % attrname)
        return self.document[attrname.replace('_', '-')]

    def __str__(self):
        objrepr = object.__repr__(self)
        buf = StringIO()
        buf.write('Fwrap configuration object:\n')
        serialized = self.serialize_to_pyx(buf)
        return buf.getvalue()

    #
    # User-facing methods
    #
    def copy(self):
        doc_copy = deepcopy(self.document)
        return Configuration(self.get_pyx_filename(), doc_copy)
    
    def update_version(self):
        self.document['version'] = get_version()

    def set_versioned_mode(self, is_versioned):
        if is_versioned:
            try:
                rev = git.cwd_rev()
            except:
                raise RuntimeError('Only git supported for now, this is not a git repository')
            self.document['vcs'] = ('git', {'head': rev})
        else:
            self.document['vcs'] = ('none', {'head': None})

    def add_wrapped_file(self, filename):
        sha1 = sha1_of_file(filename)
        self.document['wraps'].append((filename, {'sha1': sha1}))

    def wrapped_files_status(self):
        """
        Returns a report [(filename, needs_update), ...] of all
        wrapped files.
        """
        return [(filename, sha1_of_file(filename) != attrs['sha1'])
                for filename, attrs in self.wraps]

    def serialize_to_pyx(self, buf):
        parse_tree = document_to_parse_tree(self.document, self.keys)
        serialize_inline_configuration(parse_tree, buf)

    def get_source_files(self):
        return [fname for fname, attrs in self.wraps]

    def is_routine_included(self, routine_name):
        for ex_name, ex_attr in self.exclude:
            if routine_name == ex_name:
                return False
        return True

    def get_auxiliary_files(self):
        return [fname for fname, attrs in self.auxiliary]

    def git_head(self):
        if self.vcs[0] != 'git':
            raise RuntimeError('Not in git mode')
        return self.vcs[1]['head']

    def set_vcs(self, vcs, **kw):
        if vcs not in ('git', 'none'):
            raise NotImplementedError()
        for key in kw.keys():
            if not key in ('head',):
                raise TypeError('argument %s not understood' % key)
        self.document['vcs'] = (vcs, kw)

    def get_pyx_basename(self):
        return '%s.pyx' % self.wrapper_name

    def get_pyx_filename(self):
        return os.path.join(self.wrapper_path, self.get_pyx_basename())

    def get_wrapper_path(self):
        return self.wrapper_path

    def exclude_routines(self, routines):
        routines = list(routines)
        routines.sort()
        self.exclude.extend([(routine, {})
                             for routine in routines])


#
# Utils
#

def sha1_of_file(filename):
    import hashlib
    h = hashlib.sha1()
    with file(filename) as f:
        h.update(f.read())
    return h.hexdigest()    

def replace_in_file(regex_pattern, replacement, filename,
                    expected_count=None):
    with file(filename) as f:
        contents = f.read()
    contents, n = re.subn(regex_pattern, replacement, contents)
    if expected_count is not None and n != expected_count:
        raise Exception('%d replacements expected but %d possible, not changing %s' % (
            expected_count, n, filename))
    with file(filename, 'w') as f:
        f.write(contents)
    return n

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
            raise ValidationError('Unknown Fwrap configuration key: %s' % key)
        nodetype, value_parser, default, child_dom = dom[key]
        if isinstance(value_parser, str):
            value_parser = create_string_parser(value_parser)
        try:
            typed_value = value_parser(value)
        except ValueError:
            raise ValidationError('Illegal value for %s: %s' % (key, value))
        if nodetype == ATTR:
            if key in encountered or len(children) > 0:
                raise ValidationError('"%s" should only have one entry without children' % key)
            result[key] = typed_value
        elif nodetype in (LIST_ITEM, NODE):
            children_typed_tree = apply_dom(children, child_dom)
            if nodetype == NODE:
                result[key] = (typed_value, children_typed_tree)
            elif nodetype == LIST_ITEM:
                lst = result.get(key, None)
                if lst is None:
                    lst = result[key] = []
                lst.append((value, children_typed_tree))
        else:
            assert False
        encountered.add(key)
            
    # Fill in defaults
    for key in set(dom.keys()) - encountered:
        nodetype, value_parser, default, child_dom = dom[key]
        if nodetype == ATTR:
            result[key] = default
        elif nodetype == NODE:
            result[key] = (default, {})
        elif nodetype == LIST_ITEM:
            assert default is None
            result[key] = []
        else:
            assert False
    return result


def document_to_parse_tree(doc, ordered_keys):
    #TODO: ordered_keys must be on many levels,
    #      traverse DOM structure instead to serialize
    assert set(doc.keys()) == set(ordered_keys)
    result = []
    for key in ordered_keys:
        entry = doc[key]
        if isinstance(entry, list): # list-item
            for value, attrs in entry:
                subtree = document_to_parse_tree(attrs, attrs.keys())
                result.append((key, value, subtree))
        elif isinstance(entry, tuple): # node
            value, attrs = entry
            subtree = document_to_parse_tree(attrs, attrs.keys())
            result.append((key, value, subtree))
        else: # attr
            if entry is None:
                value = ''
            else:
                value = str(entry)
            result.append((key, value, []))
    return result

#
# Parsing
#
fwrap_section_re = re.compile(r'^# Fwrap:(.+)$', re.MULTILINE)
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
        buf.write('# Fwrap: %s%s %s\n' % (INDENT_STR * indent, key, value))
        serialize_inline_configuration(children, buf, indent + 1)        

#
# Global vars
#
default_cfg = Configuration(None)
default_cfg.update_version()
