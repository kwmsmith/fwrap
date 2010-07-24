# fourFn.py
#
# Demonstration of the pyparsing module, implementing a simple 4-function expression parser,
# with support for scientific notation, and symbols for e and pi.
# Extended to add exponentiation and simple built-in functions.
# Extended test cases, simplified pushFirst method.
# Removed unnecessary expr.suppress() call (thanks Nathaniel Peterson!), and added Group
# Changed fnumber to use a Regex, which is now the preferred method
#
# Copyright 2003-2009 by Paul McGuire
#
from pyparsing_py2 import Literal,CaselessLiteral,Word,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas,Regex,Combine,TokenConverter
import math
import operator

class exprprinter(object):

    def __init__(self, expr):
        self.expr = expr
        self.seen = []
        self.ident = '    '

    def visit(self):
        return self._visit(self.expr, indent=0)

    def _visit(self, node, indent):
        if isinstance(node, str):
            print self.ident*indent, repr(node)
            return
        elif node == None:
            return
        elif isinstance(node, list):
            for n in node:
                self._visit(n, indent)
            return

        try:
            node.children
        except AttributeError:
            print self.ident*indent, node
            return

        for childname in node.children:
            print self.ident*indent, childname
            child = node.children[childname]
            self._visit(child, indent+1)

class exprnode(object):

    children = []

    def __init__(self, s, loc, toks):
        self.expr = toks.asList()[:]
        self.children = {"expr" : self.expr}

    def __repr__(self):
        return repr(self.children)

class reallitconst(exprnode):

    def __init__(self, s, loc, toks):
        self.sign, self.real, self.kind = None, None, None
        toks = toks.asList()
        if toks[0] in "+-":
            self.sign, self.real = toks[0], toks[1]
        else:
            self.sign, self.real = None, toks[0]
        if len(toks) > 2:
            under, self.kind = toks[-2:]
        else:
            assert len(toks) < 4
        self.children = {"sign" : self.sign, "real" : self.real,
                         "kind" : self.kind}

class funcrefnode(exprnode):

    def __init__(self, s, loc, toks):
        self.name, self.arg_spec_list = toks.asList()[0], toks.asList()[1:]
        self.children = {"name" : self.name, "args" : self.arg_spec_list}

class funcarg(exprnode):

    def __init__(self, s, loc, toks):
        self.expr = toks.asList()[:]
        self.children = {"expr" : self.expr}

class argspec(exprnode):
     
    def __init__(self, s, loc, toks):
        self.kw = None
        if len(toks) == 3:
            self.kw, eq, self.arg = toks.asList()
        else:
            self.arg, = toks.asList()
        self.children = {"kw" : self.kw, "arg" : self.arg}

class argspeclist(exprnode):

    def __init__(self, s, loc, toks):
        self.arg_spec_list = toks.asList()[:]
        self.children = {"arg_list" : self.arg_spec_list}

fort_expr_bnf = None
def get_fort_expr_bnf():
    global fort_expr_bnf
    if fort_expr_bnf:
        return fort_expr_bnf

    expr = Forward()

    lpar = Literal("(").suppress()
    rpar = Literal(")").suppress()

    squote = Literal("'")
    dquote = Literal('"')
    under = Literal("_")
    dot = Literal(".")
    comma = Literal(",")
    concat_op = Literal("//")
    power_op = Literal("**")
    expo_letter = Regex(r"[eEdD]")
    mult_op = (Literal("*") | Literal("/"))
    sign = (Literal("+") | Literal("-"))
    add_op = sign

    name = Regex(r"[a-zA-Z]\w*")

    # int literals
    digit_string = Word(nums)
    signed_digit_string = Combine(Optional(sign) + digit_string)

    kind_param = (digit_string | name)

    int_literal_constant = ((digit_string + Optional("_" + kind_param)) | name)
    signed_int_literal_constant = (Optional(sign) + int_literal_constant)

    exponent = signed_digit_string

    # real literal
    sig1st = (digit_string + dot + Optional(digit_string))
    sig2nd = (dot + digit_string)
    significand = (sig1st | sig2nd)
    real_lit_const_1st = (Combine(significand + Optional(expo_letter + exponent)) +
                                Optional(under + kind_param))
    real_lit_const_2nd = (Combine(digit_string + expo_letter + exponent) +
                                Optional(under + kind_param))
    real_literal_constant = (real_lit_const_1st | real_lit_const_2nd)
    signed_real_literal_constant = (Optional(sign) + real_literal_constant).setParseAction(reallitconst)

    # complex literals
    cmplx_part = ( signed_real_literal_constant
                  | signed_int_literal_constant
                  | name)
    complex_literal_constant = (lpar + cmplx_part + comma + cmplx_part + rpar)

    # character literals
    rep_char = (Literal('""') | Literal("''") | Regex(r"[a-zA-Z0-9]"))
    char_literal_constant = ( (Optional(kind_param + under) +
                                squote + ZeroOrMore(rep_char) + squote)
                              | (Optional(kind_param + under) +
                                dquote + ZeroOrMore(rep_char) + dquote))

    # logical literals
    logical_literal_constant = (  CaselessLiteral(".TRUE.") + Optional(under + kind_param)
                                | CaselessLiteral(".FALSE.") + Optional(under + kind_param))

    constant = ( complex_literal_constant
                | signed_real_literal_constant
                | char_literal_constant
                | logical_literal_constant
                | signed_int_literal_constant)

    arg = (expr | name)
    arg_spec = (Optional(name + Literal("=")) + arg).setParseAction(argspec)
    arg_spec_list = (arg_spec + ZeroOrMore(comma + arg_spec))
    function_reference = (name + lpar + Optional(arg_spec_list)
                                    + rpar).setParseAction(funcrefnode)

    #R701
    primary = (function_reference ^ constant ^ name ^ Group(lpar + expr + rpar))

    #R702 we ignore defined unary ops for now.
    level1_expr = primary

    #R704 - R709
    mult_operand = Forward()
    mult_operand << (level1_expr + Optional((power_op + mult_operand)))
    add_operand = (mult_operand + ZeroOrMore(mult_op + mult_operand))
    level2_expr = (ZeroOrMore(sign) + add_operand + ZeroOrMore(add_op + add_operand))

    #R710 - R711
    level3_expr = (level2_expr + ZeroOrMore(concat_op + level2_expr))

    # We skip level 4 and level 5 expressions, since they aren't valid in a
    # dimension or ktp context.

    expr << level3_expr.setParseAction(exprnode)

    fort_expr_bnf = expr
    return fort_expr_bnf

def parser(s):
    return get_fort_expr_bnf().parseString(s, parseAll=True)

from nose.tools import eq_, ok_

class test_fort_expr(object):

    def test_int_literal(self):
        # eq_(parser("9").asList(), ['9'])
        print parser("9").asDict()
        s = str(1234567890)
        print parser(s).asDict()
        # eq_(parser(s).asList(), [s])

    def test_signed_int_lit(self):
        istr = str(310130813080138)
        s = "+%s" % istr
        print parser(s).asDict()
        # eq_(parser(s).asList(), ['+', istr])
        skp = "%s_8 + 10_abc" % s
        print parser(skp).asDict()
        print parser(skp).asList()


    def test_func_ref(self):
        ss = "foo(a, b-3+x(14), c=d+1)"
        expr = parser(ss).asList()[0]
        exprprinter(expr).visit()

    def test_reallitconst(self):
        ss = "-+12354.5678E-12_aoeu"
        expr = parser(ss).asList()[0]
        exprprinter(expr).visit()

        ss2 = ".02808_a123_45"
        expr = parser(ss2).asList()[0]
        exprprinter(expr).visit()


# test("9")
# test("-9")
# test("3.1415926")
# test("3.1415926E10")
# test("3.1415926_8")
# test("--9")
# test("-E")
# test("9 + 3 + 6")
# test("9 + 3 / 11")
# test("(9 + 3)")
# test("(9+3) / 11")
# test("9 - 12 - 6")
# test("9 - (12 - 6)")
# test("2*3.14159")
# test("3.1415926535*3.1415926535 / 10")
# test("PI * PI / 10")
# test("PI*PI/10")
# test("PI**2")
# test("round(PI**2)")
# test("6.02E23 * 8.048")
# test("e / 3")
# test("sin(PI/2)")
# test("trunc(E)")
# test("trunc(-E)")
# test("round(E)")
# test("round(-E)")
# test("E**PI")
# test("2**3**2")
# test("2**3+2")
# test("2**3+5")
# test("2**9")
# test("sgn(-2)")
# test("sgn(0)")
# test("sgn(0.1)")
# test("(0.0)")
# test("(abc, def)")
# test("(0.0, 0.0)")
# test("3 -(-(+9))")
# test("3 -(-(+(-(-(+9)))))")
# test("kind('a')")
