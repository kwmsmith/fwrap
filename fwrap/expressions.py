#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

"""
Class heirarchy of expression nodes.
"""

class ExprNode(object):
    '''
    abstract base class.
    '''
    pass

class AtomNode(ExprNode):
    pass

class AssumedShapeSpec(AtomNode):

    # child_attrs = []

    def __init__(self, s, loc, toks):
        self.star, = toks.asList()
        assert self.star == '*'

class CharLiteralConst(AtomNode):

    # child_attrs = ["kind"]

    def __init__(self, s, loc, toks):
        toks = toks.asList()
        self.kind = None
        if len(toks) == 3:
            self.kind, under, self.string = toks
        elif len(toks) == 2:
            self.kind, self.string = toks
            kind_str = self.kind.param.name
            assert kind_str.endswith('_')
            self.kind.param.name = self.kind.param.name.rstrip("_")
        elif len(toks) == 1:
            self.string, = toks
        else:
            raise ValueError("wrong number of tokens %s" % toks)

class RealLitConst(AtomNode):

    # child_attrs = ["sign", "real", "kind"]

    def __init__(self, s, loc, toks):
        self.sign, self.real, self.kind = None, None, None
        toks = toks.asList()
        if str(toks[0]) in "+-":
            self.sign, self.real = toks[0], toks[1]
        else:
            self.sign, self.real = None, toks[0]
        if len(toks) > 2:
            under, self.kind = toks[-2:]
        else:
            assert len(toks) < 4


class FuncRefNode(ExprNode):

    child_attrs = ["name", "arg_spec_list"]

    def __init__(self, s, loc, toks):
        self.name, self.arg_spec_list = toks.asList()[0], toks.asList()[1:]


class ArgSpecNode(ExprNode):

    child_attrs = ["kw", "arg"]

    def __init__(self, s, loc, toks):
        self.kw = None
        if len(toks) == 3:
            self.kw, eq, self.arg = toks.asList()
        else:
            self.arg, = toks.asList()


class KindParam(ExprNode):

    child_attrs = ["param"]

    def __init__(self, s, loc, toks):
        assert len(toks) == 1
        self.param = toks.asList()[0]


class ComplexLitConst(ExprNode):

    child_attrs = ["realpart", "imagpart"]

    def __init__(self, s, loc, toks):
        assert len(toks) == 3
        self.realpart, comma, self.imagpart = toks.asList()


class LogicalLitConst(ExprNode):

    child_attrs = ["value", "kind"]

    def __init__(self, s, loc, toks):
        if len(toks) == 3:
            self.value, under, self.kind = toks.asList()
        elif len(toks) == 1:
            self.value, self.kind = toks.asList(), None
        else:
            raise ValueError("wrong number of tokens")


class NameNode(AtomNode):

    # child_attrs = []

    def __init__(self, s, loc, toks):
        self.name = toks.asList()[0]


class SignNode(AtomNode):

    # child_attrs = []

    def __init__(self, s, loc, toks):
        self.sign, = toks.asList()

    def __str__(self):
        return str(self.sign)


class DigitStringNode(AtomNode):

    # child_attrs = []

    def __init__(self, s, loc, toks):
        self.digit_string, = toks.asList()

    def __str__(self):
        return str(self.digit_string)

class LiteralNode(AtomNode):

    # child_attrs = []

    def __init__(self, s, loc, toks):
        self.val, = toks.asList()

    def __str__(self):
        return str(self.val)

class PowerExpr(ExprNode):

    def __init__(self, s, loc, toks):
        pass

class MultExpr(ExprNode):

    def __init__(self, s, loc, toks):
        pass

class AddExpr(ExprNode):

    def __init__(self, s, loc, toks):
        pass

class StringExpr(ExprNode):

    def __init__(self, s, loc, toks):
        pass
