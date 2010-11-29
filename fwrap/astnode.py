#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

#
# Common based classes for AST nodes with various utility
# functions.
#
from inspect import isfunction, isbuiltin, ismethod

def iscallable(x):
    return isfunction(x) or isbuiltin(x) or ismethod(x)

_default_attribute_order = ['name']

def attribute_sort(attributes):
    # Sort list of attributes, preferring some attribute
    # names over others
    def key(x):
        try:
            return '%d_%s' % (_default_attribute_order.index(x), x)
        except ValueError:
            return x
    attributes.sort(key=key)
    
class AstNodeType(type):
    """
    Populate "attributes" list of node attributes, and also
    do some sanity checks.
    """
    def __init__(cls, name, bases, dct):
        super(AstNodeType, cls).__init__(name, bases, dct)
##         for key, value in dct.iteritems():
##             if isinstance(value, property):
##                 raise AssertionError('Do not use properties on AST nodes')
        if not 'attributes' in dct.keys():
            mandatory = getattr(cls, 'mandatory', None)
            if mandatory is None:
                cls.mandatory = mandatory = ()
            optional = getattr(cls, 'optional', None)
            if optional is None:
                optional = [key for key in dir(cls)
                            if not key.startswith('_') and
                            key not in mandatory and
                            not iscallable(getattr(cls, key)) and
                            not isinstance(getattr(cls, key), property) and
                            key not in ('attributes', 'mandatory', 'optional')]
                optional.sort()
                optional = tuple(optional)
                cls.optional = optional
            cls.attributes = mandatory + optional

class AstNode(object):
    __metaclass__ = AstNodeType

    @classmethod
    def create_node_from(cls, node, **kw):
        d = dict(kw)
        for attr in cls.attributes:
            if attr in d:
                continue
            if not hasattr(node, attr):
                continue            
            value = getattr(node, attr, None)
            assert not iscallable(value)
            d[attr] = value
        return cls(**d)

    def __init__(self, **kw):
        self.update(**kw)

    def update(self, **kw):
        self.validate(**kw)
        self.__dict__.update(kw)
        self._update()

    def validate(self, **kw):
        for attr in self.attributes:
            if attr not in kw and attr in self.mandatory:
                raise TypeError('Attribute %s not provided' % attr)
        self._validate(**kw)

    def _validate(self, **kw):
        """
        Override this method to raise exceptions for invalid
        assignments to node attributes. One does not have to
        check that mandatory attributes are set.
        """
        pass
 
    def _update(self):
        """
        Override this method to make changes to private attributes
        in response to changed public node attributes.
        """
        pass

    def describe(self, level=0, filter_out=(), cutoff=100, encountered=None):
        if cutoff == 0:
            return "<...nesting level cutoff...>"
        if encountered is None:
            encountered = set()
        if id(self) in encountered:
            return "<%s (%d) -- already output>" % (self.__class__.__name__, id(self))
        encountered.add(id(self))
        
        def dump_child(x, level):
            if isinstance(x, AstNode):
                return x.describe(level, filter_out, cutoff-1, encountered)
            elif isinstance(x, list):
                return "[%s]" % ", ".join([dump_child(item, level) for item in x])
            else:
                return repr(x)
                    
        def eq(x, y):
            if (isinstance(x, (list, tuple)) and
                isinstance(y, (list, tuple))
                and len(x) == len(y) == 0):
                return True
            else:
                return x == y
            
        attrs = [(key, getattr(self, key)) for key in self.attributes
                 if key not in filter_out]
        if len(attrs) == 0:
            return "<%s (%d)>" % (self.__class__.__name__, id(self))
        else:
            from fwrap.pyf_iface import Argument
            indent = "  " * level
            res = "<%s (%d)\n" % (self.__class__.__name__, id(self))
            for key, value in attrs:
                if key not in self.mandatory:
                    default = getattr(type(self), key)
                    if eq(value, default):
                        continue
                res += "%s  %s: %s\n" % (indent, key, dump_child(value, level + 1))
            res += "%s>" % indent
            return res

    def __repr__(self):
        return self.describe()
