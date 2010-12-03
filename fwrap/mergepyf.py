#------------------------------------------------------------------------------
# Copyright (c) 2010, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------
import re
from fwrap import constants
from fwrap.pyf_iface import _py_kw_mangler, py_kw_mangle_expression
from fwrap.cy_wrap import _CyArg
import pyparsing as prs

prs.ParserElement.enablePackrat()

def mergepyf_ast(cython_ast, cython_ast_from_pyf):
    # Primarily just copy ast, but merge in select detected manual
    # modifications to the pyf file present in pyf_ast

    pyf_procs = dict((proc.name, proc) for proc in cython_ast_from_pyf)
    return [mergepyf_proc(proc, pyf_procs[proc.name])
            for proc in cython_ast]

def mergepyf_proc(f_proc, pyf_proc):
    #merge_comments = []
    # There are three argument lists to merge:
    # call_args: "proc" definitely has the right one, however we
    #            may want to rename arguments
    # in_args: pyf_proc has the right one
    # out_args: pyf_proc has the right one
    #
    # Try to parse call_statement to figure out as much as
    # possible, and leave the rest to the user.

    callstat = pyf_proc.pyf_callstatement
    c_to_cython = CToCython(dict((arg.name, arg.cy_name)
                                  for arg in pyf_proc.in_args + pyf_proc.aux_args))
    if callstat is None:
        # We can simply use the pyf argument list and be satisfied
        if len(f_proc.call_args) != len(pyf_proc.call_args):
            raise ValueError('pyf and f description of function is different')
        # TODO: Verify that types match as well
        call_args = [arg.copy() for arg in pyf_proc.call_args]
    else:
        # Do NOT trust the name or order in pyf_proc.call_args,
        # but match arguments by their position in the callstatement
        pyf_args = pyf_proc.call_args + pyf_proc.aux_args
        call_args = []
        m = callstatement_re.match(callstat)
        if m is None:
            raise ValueError('Unable to parse callstatement! Have a look at callstatement_re:' +
                             callstat)
        arg_exprs = m.group(1).split(',')

        # Strip off error arguments (but leave return value)
        assert f_proc.call_args[-2].name == constants.ERR_NAME
        assert f_proc.call_args[-1].name == constants.ERRSTR_NAME
        fortran_args = f_proc.call_args[:-2]
        if len(fortran_args) != len(arg_exprs):
            raise ValueError('"%s": pyf and f disagrees, '
                             'len(fortran_args) != len(arg_exprs)' % pyf_proc.name)
        # Build call_args from the strings present in the callstatement
        for idx, (f_arg, expr) in enumerate(zip(fortran_args, arg_exprs)):
            if idx == 0 and pyf_proc.kind == 'function':
                # NOT the same as f_proc.kind == 'function'
                
                # We can't resolve by name for the return arg, but it will
                # always be first. This case does not hit for functions
                # declared as subprocs in pyf, where the return arg *can*
                # be reorderd, but also carries a user-given name for matching.
                arg = pyf_proc.call_args[0].copy()
            else:
                arg = parse_callstatement_arg(expr, f_arg, pyf_args, c_to_cython)
            call_args.append(arg)
            
        # Reinsert the extra error-handling and function return arguments
        call_args.append(f_proc.call_args[-2].copy())
        call_args.append(f_proc.call_args[-1].copy())

    # Make sure our three lists (in/out/callargs) contain the same
    # argument objects
    all_args = dict((arg.name, arg) for arg in call_args)
    def copy_or_get(arg):
        result = all_args.get(arg.name, None)
        if result is None:
            result = arg.copy()
        return result

    in_args = [copy_or_get(arg) for arg in pyf_proc.in_args]
    out_args = [copy_or_get(arg) for arg in pyf_proc.out_args]
    in_args = process_in_args(in_args, c_to_cython)
    result = f_proc.copy_and_set(call_args=call_args,
                                 in_args=in_args,
                                 out_args=out_args,
                                 aux_args=pyf_proc.aux_args,
                                 language='pyf')
    return result

callstatement_re = re.compile(r'^.*\(\*f2py_func\)\s*\((.*)\).*$')
callstatement_arg_re = re.compile(r'^\s*(&)?\s*([a-zA-Z0-9_]+)(\s*\+\s*([a-zA-Z0-9_]+))?\s*$')
nested_ternary_re = re.compile(r'^\(?(\s*\(\) .*)\?(.*):(.*)\)?$')

def parse_callstatement_arg(arg_expr, f_arg, pyf_args, c_to_cython):
    # Parse arg_expr, and return a suitable new argument based on pyf_args
    # Returns None for unparseable/too complex expression
    m = callstatement_arg_re.match(arg_expr)
    if m is not None:
        ampersand, var_name, offset = m.group(1), m.group(2), m.group(4)
        if offset is not None and ampersand is not None:
            raise ValueError('Arithmetic on scalar pointer?')
        pyf_arg = [arg for arg in pyf_args if arg.name == var_name]
        if len(pyf_arg) >= 1:
            result = pyf_arg[0].copy()
            if offset is not None:
                if not result.is_array:
                    raise ValueError('Passing scalar without taking address?')
                result.update(mem_offset_code=_py_kw_mangler(offset))
            return result
        else:
            return manual_arg(f_arg, arg_expr)
    else:
        try:
            cy_expr, depends = c_to_cython.translate(arg_expr)
        except ValueError:
            return manual_arg(f_arg, arg_expr)
        else:
            return auxiliary_arg(f_arg, cy_expr)

def manual_arg(f_arg, expr):
    # OK, we do not understand the C code in the callstatement in this
    # argument position, but at least introduce a temporary variable
    # and put in a placeholder for user intervention
    return auxiliary_arg(f_arg, '##TODO: %s' % expr)

def auxiliary_arg(f_arg, expr):
    arg = f_arg.copy_and_set(
        cy_name='%s_f' % f_arg.name,
        name='%s_f' % f_arg.name,
        intent=None,
        pyf_hide=True,
        pyf_default_value=expr)
    return arg

literal_re = re.compile(r'^-?[()0-9.,\s]+$') # close enough; also matches e.g. (0, 0.)
#default_array_value_re = re.compile(r'^[()0.,\s]+$') # variations of zero...

def process_in_args(in_args, c_to_cython):
    # Arguments must be changed as follows:
    # a) Reorder so that arguments with defaults come last
    # b) Parse the default_value into something usable by Cython.
    for arg in in_args:
        if arg.pyf_check is not None:
            arg.update(pyf_check=[c_to_cython.translate(c)[0]
                                  for c in arg.pyf_check])
    
    mandatory = [arg for arg in in_args if not arg.is_optional()]
    optional = [arg for arg in in_args if arg.is_optional()]
    in_args = mandatory + optional

    for arg in optional:
        default_value = arg.pyf_default_value
        if (default_value is not None and
            literal_re.match(default_value) is None):
            # Do some crude processing of default_value to translate
            # it fully or partially to Cython
            default_value, depends = c_to_cython.translate(default_value)
            arg.update(defer_init_to_body=True,
                       pyf_default_value=default_value)

    
    # Process intent(copy) and intent(overwrite). f2py behaviour is to
    # add overwrite_X to the very end of the argument list, so insert
    # new argument nodes.
    overwrite_args = []
    for arg in in_args:
        if arg.pyf_overwrite_flag:
            flagname = 'overwrite_%s' % arg.cy_name
            arg.overwrite_flag_cy_name = flagname
            overwrite_args.append(
                _CyArg(name=flagname,
                       cy_name=flagname,
                       ktp='bint',
                       intent='in',
                       dtype=None,
                       pyf_default_value=repr(arg.pyf_overwrite_flag_default)))
    in_args.extend(overwrite_args)

    # Return new set of in_args
    return in_args


class CToCython(object):
    def __init__(self, variable_map=None):
        self.variable_map = variable_map

        def handle_var(s, loc, tok):
            v = tok[0]
            self.encountered.add(v)
            if self.variable_map is None:
                return _py_kw_mangler(tok[0])
            else:
                return self.variable_map[tok[0]]
            

        # FollowedBy(NotAny): make sure variables and
        # function calls are not confused
        variables = prs.Regex(r'[a-zA-Z_][a-zA-Z0-9_]*') + prs.FollowedBy(prs.NotAny('('))
        variables.setParseAction(handle_var)

        var_or_literal = variables | prs.Regex('-?[0-9.]+') | prs.dblQuotedString

        def handle_ternary(s, loc, tok):
            tok = tok[0]
            return '(%s if %s else %s)' % (tok[2], tok[0], tok[4])

        def passthrough_op(s, loc, tok):
            return '(%s)' % ' '.join(tok[0])

        _c_to_cython_bool = {'&&' : 'and', '||' : 'or', '/' : '//', '*' : '*'}
        def translate_op(s, loc, tok):
            tok = tok[0]
            translated = [x if idx % 2 == 0 else _c_to_cython_bool[x]
                          for idx, x in enumerate(tok)]
            return '(%s)' % (' '.join(translated))

        def handle_not(s, loc, tok):
            return 'not %s' % tok[0][1]

        def handle_cast(s, loc, tok):
            return '<%s>%s' % (tok[0][0], tok[0][1])

        def handle_func(s, loc, tok):
            func, args = tok[0], tok[1:]
            if func == 'len':
                return 'np.PyArray_DIMS(%s)[0]' % args[0]
            elif func == 'shape':
                return 'np.PyArray_DIMS(%s)[%s]' % (args[0], args[1])
            elif func in ('abs',):
                return '%s(%s)' % (func, ', '.join(args))

        expr = prs.Forward()

        func_call = (prs.oneOf('len shape abs') + prs.Suppress('(') + expr +
                     prs.ZeroOrMore(prs.Suppress(',') + expr) + prs.Suppress(')'))
        func_call.setParseAction(handle_func)
        cast = prs.Suppress('(') + prs.oneOf('int float') + prs.Suppress(')')

        expr << prs.operatorPrecedence(var_or_literal | func_call, [
            ('!', 1, prs.opAssoc.RIGHT, handle_not),
            (cast, 1, prs.opAssoc.RIGHT, handle_cast),
            (prs.oneOf('* /'), 2, prs.opAssoc.LEFT, translate_op),
            (prs.oneOf('+ -'), 2, prs.opAssoc.LEFT, passthrough_op),
            (prs.oneOf('== != <= >= < >'), 2, prs.opAssoc.LEFT, passthrough_op),
            (prs.oneOf('|| &&'), 2, prs.opAssoc.LEFT, translate_op),
            (('?', ':'), 3, prs.opAssoc.RIGHT, handle_ternary),
            ]) 

        self.translator = expr + prs.StringEnd()

    def translate(self, s):
        self.encountered = set()
        try:
            r = self.translator.parseString(s)[0]
        except prs.ParseException, e:
            raise ValueError('Could not auto-translate: %s (%s)' % (s, e))            
        if r[0] == '(' and r[-1] == ')':
            r = r[1:-1]
        return r, self.encountered

