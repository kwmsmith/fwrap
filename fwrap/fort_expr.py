#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# Modifed beyond all recognition from example parser in fourFn.py, distributed
# with pyparsing.
#
# Original fourFn.py is Copyright 2003-2009 by Paul McGuire


from pyparsing_py2 import (Literal, CaselessLiteral, Word, Group, Optional,
        ZeroOrMore, Forward, nums, alphas, Regex, Combine, TokenConverter,
        QuotedString, FollowedBy, Empty)

from visitor import TreeVisitor

tp2ord = {
    "TP_MIN" : -1000,
    "integer" : 0,
    "real"    : 1,
    "complex" : 2
}
TP_MIN = "TP_MIN"
def resolve_number_cast(types):
    max_tp = TP_MIN
    for tp in types:
        if tp_cast[tp] > tp_cast[max_tp]:
            max_tp = tp
    return max_tp

class ExpressionType(TreeVisitor):

    def __init__(self, ctx):
        super(ExpressionType, self).__init__()
        self.ctx = ctx
        self.stack = []

    def visit_ExprNode(self, node):
        pass
        # if len(node.subexpr) > 1:
            # # FIXME: this obviously doesn't work right...
            # raise NotImplementedError("non-trivial expressions not currently supported")
        # return self.visit(node.subexpr[0])

    def visit_FuncRefNode(self, node):
        pass

    def _generic_composite_expr_resolve(self, node):
        arg_types = [self.visit(arg) for arg in node.args]
        return resolve_number_cast(arg_types)

    visit_AddExpr = _generic_composite_expr_resolve
    visit_MultExpr = _generic_composite_expr_resolve
    visit_PowerExpr = _generic_composite_expr_resolve
    visit_ConcatExpr = _generic_composite_expr_resolve

    # def visit_AddExpr(self, node):
        # arg_types = [self.visit(arg) for arg in node.args]
        # return resolve_number_cast(arg_types)

    def visit_MultExpr(self, node):
        pass

    def visit_PowerExpr(self, node):
        pass

    def visit_ConcatExpr(self, node):
        pass

    def visit_ArgSpecNode(self, node):
        return self.visit(node.arg)

    def visit_NameNode(self, node):
        return self.ctx[node.name]

class ExtractNames(TreeVisitor):

    def __init__(self):
        super(ExtractNames, self).__init__()
        self.namenodes = []
        self.funcnamenodes = []

    visit_ExprNode = TreeVisitor.visitchildren

    #XXX: slight hack here...
    visit_str = lambda self, x: None

    def visit_FuncRefNode(self, node):
        self.funcnamenodes.append(node.name)
        self.visitchildren(node, ["arg_spec_list"])

    def visit_NameNode(self, node):
        self.namenodes.append(node)

    def visit_ArgSpecNode(self, node):
        self.visitchildren(node, ["arg"])

    def _get_names(self):
        return [node.name for node in self.namenodes]
    names = property(_get_names)

    def _get_funcnames(self):
        return [node.name for node in self.funcnamenodes]
    funcnames = property(_get_funcnames)



class ExprNode(object):
    '''
    abstract base class.
    '''
    child_attrs = []

class EmptyNode(ExprNode):

    child_attrs = []

    def __init__(self, s, loc, toks):
        pass

class AtomNode(ExprNode):
    pass

class AssumedShapeSpec(AtomNode):

    child_attrs = []

    def __init__(self, s, loc, toks):
        self.star, = toks.asList()
        assert self.star == '*'

class CharLiteralConst(AtomNode):

    child_attrs = ["kind"]

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

    child_attrs = ["sign", "real", "kind"]

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

    child_attrs = []

    def __init__(self, s, loc, toks):
        self.name = toks.asList()[0]


class SignNode(AtomNode):

    child_attrs = []

    def __init__(self, s, loc, toks):
        self.sign, = toks.asList()

    def __str__(self):
        return str(self.sign)


class DigitStringNode(AtomNode):

    child_attrs = []

    def __init__(self, s, loc, toks):
        self.digit_string, = toks.asList()

    def __str__(self):
        return str(self.digit_string)

class LiteralNode(AtomNode):

    child_attrs = []

    def __init__(self, s, loc, toks):
        self.val, = toks.asList()

    def __str__(self):
        return str(self.val)

class PowerExpr(ExprNode):

    child_attrs = ["args"]

    def __new__(cls, s, loc, toks):
        if len(toks) == 1:
            # this is an unnecessary wrapper, so just return toks[0]
            return toks[0]
        else:
            return super(PowerExpr, cls).__new__(cls)

    def __init__(self, s, loc, toks):
        self.args = [tok for tok in toks if not isinstance(tok, LiteralNode)]
        self.ops =  [tok for tok in toks if isinstance(tok, LiteralNode)]

class MultExpr(ExprNode):

    child_attrs = ["args"]

    def __new__(cls, s, loc, toks):
        if len(toks) == 1:
            # this is an unnecessary wrapper, so just return toks[0]
            return toks[0]
        else:
            return super(MultExpr, cls).__new__(cls)

    def __init__(self, s, loc, toks):
        self.args = [tok for tok in toks if isinstance(tok, PowerExpr)]
        self.ops =  [tok for tok in toks if not isinstance(tok, PowerExpr)]

class AddExpr(ExprNode):

    child_attrs = ["args"]

    def __new__(cls, s, loc, toks):
        if len(toks) == 1:
            # this is an unnecessary wrapper, so just return toks[0]
            return toks[0]
        else:
            return super(AddExpr, cls).__new__(cls)

    def __init__(self, s, loc, toks):
        self.args = [tok for tok in toks if isinstance(tok, MultExpr)]
        self.ops =  [tok for tok in toks if not isinstance(tok, MultExpr)]

class ConcatExpr(ExprNode):

    child_attrs = ["args"]

    def __new__(cls, s, loc, toks):
        if len(toks) == 1:
            # this is an unnecessary wrapper, so just return toks[0]
            return toks[0]
        else:
            return super(ConcatExpr, cls).__new__(cls)

    def __init__(self, s, loc, toks):
        self.args = [tok for tok in toks if isinstance(tok, AddExpr)]
        self.ops =  [tok for tok in toks if not isinstance(tok, AddExpr)]


fort_expr_bnf = None
def get_fort_expr_bnf():
    global fort_expr_bnf
    if fort_expr_bnf:
        return fort_expr_bnf

    expr = Forward()

    lpar = Literal("(").suppress()
    rpar = Literal(")").suppress()

    under = Literal("_").setParseAction(LiteralNode)
    dot = Literal(".").setParseAction(LiteralNode)
    comma = Literal(",").setParseAction(LiteralNode)
    concat_op = Literal("//")
    power_op = Literal("**")
    expo_letter = Regex(r"[eEdD]")
    mult_op = (Literal("*") | Literal("/"))
    sign = (Literal("+") | Literal("-")).setParseAction(SignNode)
    add_op = sign

    name = Regex(r"[a-zA-Z]\w*").setParseAction(NameNode)

    # int literals
    digit_string = Word(nums).setParseAction(DigitStringNode)
    signed_digit_string = Combine(Optional(sign) + digit_string)

    kind_param = (digit_string | name).setParseAction(KindParam)

    int_literal_constant = ((digit_string + Optional("_" + kind_param)) | name)
    signed_int_literal_constant = (Optional(sign) + int_literal_constant)

    exponent = signed_digit_string

    # real literal
    sig1st = (digit_string + dot + Optional(digit_string))
    sig2nd = (dot + digit_string)
    significand = (sig1st | sig2nd)
    real_lit_const_1st = (Combine(
                            significand +
                            Optional(expo_letter + exponent)) +
                          Optional(under + kind_param))

    real_lit_const_2nd = (Combine(
                            digit_string +
                            expo_letter +
                            exponent) +
                          Optional(under + kind_param))
    real_literal_constant = (real_lit_const_1st | real_lit_const_2nd)
    signed_real_literal_constant = \
            (Optional(sign) +
                real_literal_constant).setParseAction(RealLitConst)

    # complex literals
    cmplx_part = ( signed_real_literal_constant
                  | signed_int_literal_constant
                  | name)
    complex_literal_constant = \
            (lpar + cmplx_part +
                    comma + cmplx_part + rpar).setParseAction(ComplexLitConst)

    # character literals
    squotedString = QuotedString(quoteChar="'", escQuote="''")
    dquotedString = QuotedString(quoteChar='"', escQuote='""')

    #XXX: this is kind of cheating...
    char_literal_constant = \
            (Optional(kind_param + Optional("_")) +
              (squotedString | dquotedString)).setParseAction(CharLiteralConst)

    # logical literals
    logical_literal_constant = \
            ( (CaselessLiteral(".TRUE.") +
                    Optional(under + kind_param))
             | (CaselessLiteral(".FALSE.") +
                 Optional(under + kind_param))).setParseAction(LogicalLitConst)

    constant = (  char_literal_constant
                | complex_literal_constant
                | signed_real_literal_constant
                | logical_literal_constant
                | signed_int_literal_constant)

    arg = (expr | name)
    arg_spec = (Optional(name + Literal("="))
                        + arg).setParseAction(ArgSpecNode)
    arg_spec_list = (arg_spec + ZeroOrMore(comma.suppress() + arg_spec))
    function_reference = (name + lpar + Optional(arg_spec_list)
                                    + rpar).setParseAction(FuncRefNode)

    #R701
    primary = (function_reference ^ constant ^ name ^ (lpar + expr + rpar))

    #R702 we ignore defined unary ops for now.
    level1_expr = primary

    #R704 - R709
    mult_operand = Forward()
    mult_operand << (level1_expr + Optional((power_op + mult_operand))).setParseAction(PowerExpr)
    add_operand = (mult_operand + ZeroOrMore(mult_op + mult_operand)).setParseAction(MultExpr)
    level2_expr = (ZeroOrMore(sign) +
                        add_operand + ZeroOrMore(add_op + add_operand)).setParseAction(AddExpr)

    #R710 - R711
    level3_expr = (level2_expr + ZeroOrMore(concat_op + level2_expr)).setParseAction(ConcatExpr)

    # We skip level 4 and level 5 expressions, since they aren't valid in a
    # dimension or ktp context.

    expr << ( level3_expr
            | Literal('*').setParseAction(AssumedShapeSpec)
            | Empty().setParseAction(EmptyNode))

    fort_expr_bnf = expr
    return fort_expr_bnf

def parse(s):
    return get_fort_expr_bnf().parseString(s, parseAll=False).asList()[0]
