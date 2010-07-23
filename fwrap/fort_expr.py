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
from pyparsing import Literal,CaselessLiteral,Word,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas,Regex
import math
import operator

stack = []

def pushInt(strg, loc, toks):
    # import pdb; pdb.set_trace()
    pass

def pushReal(strg, loc, toks):
    # import pdb; pdb.set_trace()
    pass

def pushCmplx(strg, loc, toks):
    # import pdb; pdb.set_trace()
    pass

def pushChar(strg, loc, toks):
    # import pdb; pdb.set_trace()
    pass

fort_expr_bnf = None
def get_fort_expr_bnf():
    global fort_expr_bnf
    if fort_expr_bnf:
        return fort_expr_bnf

    def _re_grp(s):
        return r"(:?%s)" % s

    def _re_opt(s):
        return _re_grp(s) + r"?"

    def _re_or(s1, s2):
        return r"(:?%s|%s)" % (s1, s2)

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
    mult_op = (Literal("*") | Literal("/"))
    sign = (Literal("+") | Literal("-"))
    add_op = sign

    name_re = r"[a-zA-Z]\w*"
    name = Regex(name_re)

    # int literals
    digit_string_re = _re_grp(r"[0-9]+")
    digit_string = Regex(digit_string_re)
    opt_sign_re = _re_grp(r"[+-]?")

    signed_digit_string_re = opt_sign_re + digit_string_re
    signed_digit_string = Regex(signed_digit_string_re)

    kind_param_re = _re_or(digit_string_re, name_re)
    kind_param = Regex(kind_param_re)

    under_re = r"_"
    _1st_re = digit_string_re + _re_opt(under_re +  kind_param_re)
    int_literal_constant_re = _re_or(_1st_re, name_re)
    signed_int_literal_constant_re = _re_grp(opt_sign_re + int_literal_constant_re)
    print signed_int_literal_constant_re
    int_literal_constant = Regex(int_literal_constant_re)
    signed_int_literal_constant = Regex(signed_int_literal_constant_re).setParseAction(pushInt)

    # real literals
    exponent_re = signed_digit_string_re
    expo_letter_re = _re_grp(r"[eEdD]")
    sig1st_re = _re_grp(digit_string_re + r"\." + _re_opt(digit_string_re))
    sig2nd_re = _re_grp(r"\." + digit_string_re)
    significand_re = _re_or(sig1st_re, sig2nd_re)
    real_lit_const_1st_re = _re_grp(
                                significand_re +
                                _re_opt(
                                     expo_letter_re + exponent_re) +
                                _re_opt(under_re + kind_param_re))
    real_lit_const_2nd_re = _re_grp(
                                digit_string_re + expo_letter_re + exponent_re +
                                _re_opt(under_re + kind_param_re))
    real_literal_constant_re = _re_or(real_lit_const_1st_re, real_lit_const_2nd_re)
    real_literal_constant = Regex(real_literal_constant_re)
    signed_real_literal_constant_re = _re_grp(opt_sign_re + real_literal_constant_re)
    print signed_real_literal_constant_re
    signed_real_literal_constant = Regex(signed_real_literal_constant_re).setParseAction(pushReal)

    # complex literals
    cmplx_part = ( signed_real_literal_constant
                  | signed_int_literal_constant
                  | name)
    complex_literal_constant = (lpar + cmplx_part + comma + cmplx_part + rpar).setParseAction(pushCmplx)

    # character literals
    rep_char = (Literal('""') | Literal("''") | Regex(r"[a-zA-Z0-9]"))
    char_literal_constant = ( (Optional(kind_param + under) +
                                squote + ZeroOrMore(rep_char) + squote)
                              | (Optional(kind_param + under) +
                                dquote + ZeroOrMore(rep_char) + dquote)).setParseAction(pushChar)

    # logical literals
    logical_literal_constant = (  CaselessLiteral(".TRUE.") + Optional(under + kind_param)
                                | CaselessLiteral(".FALSE.") + Optional(under + kind_param))

    constant = ( complex_literal_constant
                | signed_real_literal_constant
                | char_literal_constant
                | logical_literal_constant
                | signed_int_literal_constant)

    arg = (expr | name)
    arg_spec = (Optional(name + Literal("=")) + arg)
    arg_spec_list = (arg_spec + ZeroOrMore(comma + arg_spec))
    function_reference = (name + Group(lpar + Optional(arg_spec_list) + rpar))

    #R701
    # primary = (ZeroOrMore(sign) + (function_reference | constant | name) | Group(lpar + expr + rpar))
    primary = (ZeroOrMore(sign) + (function_reference | constant | name | Group(lpar + expr + rpar)))

    #R702 we ignore defined unary ops for now.
    level1_expr = primary

    #R704 - R709
    mult_operand = Forward()
    mult_operand << (level1_expr + Optional((power_op + mult_operand)))
    add_operand = (mult_operand + ZeroOrMore(mult_op + mult_operand))
    level2_expr = (add_operand + ZeroOrMore(add_op + add_operand))

    #R710 - R711
    level3_expr = (level2_expr + ZeroOrMore(concat_op + level2_expr))

    # We skip level 4 and level 5 expressions, since they aren't valid in a
    # dimension or ktp context.

    expr << level3_expr

    fort_expr_bnf = expr
    return fort_expr_bnf


# bnf = None
# def BNF():
    # """
    # expop   :: '**'
    # multop  :: '*' | '/'
    # addop   :: '+' | '-'
    # integer :: ['+' | '-'] '0'..'9'+
    # atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
    # factor  :: atom [ expop factor ]*
    # term    :: factor [ multop factor ]*
    # expr    :: term [ addop term ]*
    # """
    # global bnf
    # if not bnf:
        # point = Literal( "." )
        # e     = CaselessLiteral( "E" )
        # #~ fnumber = Combine( Word( "+-"+nums, nums ) +
                           # #~ Optional( point + Optional( Word( nums ) ) ) +
                           # #~ Optional( e + Word( "+-"+nums, nums ) ) )
        # fnumber = Regex(r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?")
        # ident = Word(alphas, alphas+nums+"_$")

        # plus  = Literal( "+" )
        # minus = Literal( "-" )
        # mult  = Literal( "*" )
        # div   = Literal( "/" )
        # lpar  = Literal( "(" ).suppress()
        # rpar  = Literal( ")" ).suppress()
        # addop  = plus | minus
        # multop = mult | div
        # expop = Literal( "**" )
        # pi    = CaselessLiteral( "PI" )

        # expr = Forward()
        # # atom = (Optional("-") + ( pi | e | fnumber | ident + lpar + expr +
        # # rpar ).setParseAction( pushFirst ) |
        # atom = (Optional("-") + ( pi | e | fnumber | ident + lpar + expr + rpar ) |
                # Group( lpar + expr + rpar ))

        # # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom
        # # [ ^ atom ]...", we get right-to-left exponents, instead of
        # # left-to-right
        # # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        # factor = Forward()
        # factor << (atom + ZeroOrMore( ( expop + factor )))

        # term = factor + ZeroOrMore( ( multop + factor ))
        # expr << (term + ZeroOrMore( ( addop + term )))
        # bnf = expr
    # return bnf

if __name__ == "__main__":

    def test(s):
        global exprStack
        results = get_fort_expr_bnf().parseString(s)
        print s, results

    test("9")
    test("-9")
    test("3.1415926")
    test("3.1415926E10")
    test("3.1415926_8")
    test("--9")
    test("-E")
    test("9 + 3 + 6")
    test("9 + 3 / 11")
    test("(9 + 3)")
    test("(9+3) / 11")
    test("9 - 12 - 6")
    test("9 - (12 - 6)")
    test("2*3.14159")
    test("3.1415926535*3.1415926535 / 10")
    test("PI * PI / 10")
    test("PI*PI/10")
    test("PI**2")
    test("round(PI**2)")
    test("6.02E23 * 8.048")
    test("e / 3")
    test("sin(PI/2)")
    test("trunc(E)")
    test("trunc(-E)")
    test("round(E)")
    test("round(-E)")
    test("E**PI")
    test("2**3**2")
    test("2**3+2")
    test("2**3+5")
    test("2**9")
    test("sgn(-2)")
    test("sgn(0)")
    test("sgn(0.1)")
    test("(0.0)")
    test("(abc, def)")
    test("(0.0, 0.0)")
    test("3 -- (+9)")
    test("3 --+--(+9)")
    test("kind('a')")
