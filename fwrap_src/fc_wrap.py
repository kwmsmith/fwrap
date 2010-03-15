import inspect
from fwrap_src import pyf_iface as pyf

KTP_MOD_NAME = "fwrap_ktp_mod"

class SourceGenerator(object):

    def __init__(self, basename):
        self.basename = basename
        self.filename = self._fname_template % basename

    def generate(self, program_unit_list, buf):
        raise NotImplementedError()

class GenPxd(SourceGenerator):

    _fname_template = "%s_c.pxd"

    def generate(self, program_unit_list, buf):
        buf.write('''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''
    )

class GenCHeader(SourceGenerator):

    _fname_template = "%s_c.h"

    def generate(self, program_unit_list, buf):
        buf.write('''
#include "config.h"
fwrap_default_int empty_func_c();
'''
    )

class BasicVisitor(object):
    """A generic visitor base class which can be used for visiting any kind of object."""
    def __init__(self):
        self.dispatch_table = {}

    def visit(self, obj):
        cls = type(obj)
        try:
            handler_method = self.dispatch_table[cls]
        except KeyError:
            #print "Cache miss for class %s in visitor %s" % (
            #    cls.__name__, type(self).__name__)
            # Must resolve, try entire hierarchy
            pattern = "visit_%s"
            mro = inspect.getmro(cls)
            handler_method = None
            for mro_cls in mro:
                if hasattr(self, pattern % mro_cls.__name__):
                    handler_method = getattr(self, pattern % mro_cls.__name__)
                    break
            if handler_method is None:
                print type(self), type(obj)
                if hasattr(self, 'access_path') and self.access_path:
                    print self.access_path
                    if self.access_path:
                        print self.access_path[-1][0].pos
                        print self.access_path[-1][0].__dict__
                raise RuntimeError("Visitor does not accept object: %s" % obj)
            #print "Caching " + cls.__name__
            self.dispatch_table[cls] = handler_method
        return handler_method(obj)

class TreeVisitor(BasicVisitor):
    """
    Base class for writing visitors for a Cython tree, contains utilities for
    recursing such trees using visitors. Each node is
    expected to have a content iterable containing the names of attributes
    containing child nodes or lists of child nodes. Lists are not considered
    part of the tree structure (i.e. contained nodes are considered direct
    children of the parent node).
    
    visit_children visits each of the children of a given node (see the visit_children
    documentation). When recursing the tree using visit_children, an attribute
    access_path is maintained which gives information about the current location
    in the tree as a stack of tuples: (parent_node, attrname, index), representing
    the node, attribute and optional list index that was taken in each step in the path to
    the current node.
    
    Example:
    
    >>> class SampleNode(object):
    ...     child_attrs = ["head", "body"]
    ...     def __init__(self, value, head=None, body=None):
    ...         self.value = value
    ...         self.head = head
    ...         self.body = body
    ...     def __repr__(self): return "SampleNode(%s)" % self.value
    ...
    >>> tree = SampleNode(0, SampleNode(1), [SampleNode(2), SampleNode(3)])
    >>> class MyVisitor(TreeVisitor):
    ...     def visit_SampleNode(self, node):
    ...         print "in", node.value, self.access_path
    ...         self.visitchildren(node)
    ...         print "out", node.value
    ...
    >>> MyVisitor().visit(tree)
    in 0 []
    in 1 [(SampleNode(0), 'head', None)]
    out 1
    in 2 [(SampleNode(0), 'body', 0)]
    out 2
    in 3 [(SampleNode(0), 'body', 1)]
    out 3
    out 0
    """
    
    def __init__(self):
        super(TreeVisitor, self).__init__()
        self.access_path = []

    def __call__(self, tree):
        self.visit(tree)
        return tree

    def visitchild(self, child, parent, idx):
        self.access_path.append((parent, idx))
        result = self.visit(child)
        self.access_path.pop()
        return result

    def visitchildren(self, parent, attrs=None):
        """
        Visits the children of the given parent. If parent is None, returns
        immediately (returning None).
        
        The return value is a dictionary giving the results for each
        child (mapping the attribute name to either the return value
        or a list of return values (in the case of multiple children
        in an attribute)).
        """

        if parent is None: return None
        content = getattr(parent, 'content', None)
        if content is None or not isinstance(content, list):
            return None
        result = [self.visitchild(child, parent, idx) for (idx, child) in \
                enumerate(content)]
        return result

def generate_interface(proc, gmn, buf):
        buf.putln('interface')
        buf.indent()
        buf.putln(proc.procedure_decl())
        buf.indent()
        proc.proc_preamble(gmn, buf)
        buf.dedent()
        buf.putln(proc.procedure_end())
        buf.dedent()
        buf.putln('end interface')

class ProcWrapper(object):

    def procedure_end(self):
        return "end %s %s" % (self.kind, self.name)

    def proc_preamble(self, ktp_mod, buf):
        buf.putln('use %s' % ktp_mod)
        buf.putln('implicit none')
        for decl in self.arg_declarations():
            buf.putln(decl)

    def generate_wrapper(self, gmn, buf):
        buf.putln(self.procedure_decl())
        buf.indent()
        self.proc_preamble(gmn, buf)
        generate_interface(self.wrapped, gmn, buf)
        # self.wrapped.generate_interface(buf)
        self.declare_temps(buf)
        self.pre_call_code(buf)
        self.proc_call(buf)
        self.post_call_code(buf)
        buf.dedent()
        buf.putln(self.procedure_end())

    def procedure_decl(self):
        return '%s %s(%s) bind(c, name="%s")' % \
                (self.kind, self.name,
                        ', '.join(self.extern_arg_list()),
                        self.name)

    def declare_temps(self, buf):
        for decl in self.temp_declarations():
            buf.putln(decl)

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def temp_declarations(self):
        return self.arg_man.temp_declarations()

    def pre_call_code(self, buf):
        for line in self.arg_man.pre_call_code():
            buf.putln(line)

    def post_call_code(self, buf):
        for line in self.arg_man.post_call_code():
            buf.putln(line)

    def proc_call(self, buf):
        proc_call = "%s(%s)" % (self.wrapped.name,
                                ', '.join(self.call_arg_list()))
        if isinstance(self, SubroutineWrapper):
            buf.putln("call %s" % proc_call)
        elif isinstance(self, FunctionWrapper):
            buf.putln("%s = %s" % (self.proc_result_name(), proc_call))

    def call_arg_list(self):
        return self.arg_man.call_arg_list()

class FunctionWrapper(ProcWrapper):

    def __init__(self, name, wrapped):
        self.kind = 'function'
        self.name = name
        self.wrapped = wrapped
        ra = pyf.Argument(name=name, dtype=wrapped.return_arg.dtype, intent='out', is_return_arg=True)
        self.arg_man = ArgWrapperManager(wrapped._args, ra)

    def return_spec_declaration(self):
        return self.arg_man.return_spec_declaration()

    def proc_result_name(self):
        return self.arg_man.return_var_name()

class SubroutineWrapper(ProcWrapper):

    def __init__(self, name, wrapped):
        self.kind = 'subroutine'
        self.name = name
        self.wrapped = wrapped
        self.arg_man = ArgWrapperManager(wrapped._args)

class ArgWrapperManager(object):
    
    def __init__(self, args, return_arg=None):
        self._orig_args = args
        self._orig_return_arg = return_arg
        self.arg_wrappers = None
        self.return_arg_wrapper = None
        self._gen_wrappers()

    def _gen_wrappers(self):
        wargs = []
        for arg in self._orig_args:
            wargs.append(ArgWrapperFactory(arg))
        self.arg_wrappers = wargs
        arg = self._orig_return_arg
        if arg:
            self.return_arg_wrapper = ArgWrapperFactory(arg)

    def call_arg_list(self):
        cl = []
        for argw in self.arg_wrappers:
            cl.append(argw.intern_name())
        return cl

    def extern_arg_list(self):
        ret = []
        for argw in self.arg_wrappers:
            ret.extend(argw.extern_arg_list())
        return ret

    def arg_declarations(self):
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.extern_declarations())
        if self.return_arg_wrapper:
            decls.extend(self.return_arg_wrapper.extern_declarations())
        return decls

    def __return_spec_declaration(self):
        #XXX: demeter ???
        return self.return_arg_wrapper.extern_arg.declaration()

    def temp_declarations(self):
        #XXX: demeter ???
        decls = []
        for argw in self.arg_wrappers:
            decls.extend(argw.intern_declarations())
        if self.return_arg_wrapper:
            decls.extend(self.return_arg_wrapper.intern_declarations())
        return decls

    def pre_call_code(self):
        all_pcc = []
        for argw in self.arg_wrappers:
            pcc = argw.pre_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def post_call_code(self):
        all_pcc = []
        wpprs = self.arg_wrappers
        if self.return_arg_wrapper:
            wpprs.append(self.return_arg_wrapper)
        for argw in wpprs:
            pcc = argw.post_call_code()
            if pcc:
                all_pcc.extend(pcc)
        return all_pcc

    def return_var_name(self):
        return self.return_arg_wrapper.intern_name()

def ArgWrapperFactory(arg):
    if getattr(arg, 'dimension', None):
        return ArrayArgWrapper(arg)
    elif arg.intent == 'hide':
        return HideArgWrapper(arg)
    else:
        return ArgWrapper(arg)

class ArgWrapperBase(object):

    def pre_call_code(self):
        return []

    def post_call_code(self):
        return []

    def intern_declarations(self):
        return []

class ArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_arg = arg
        self._intern_var = None

    def intern_name(self):
        if self._intern_var:
            return self._intern_var.name
        else:
            return self._extern_arg.name

    def extern_arg_list(self):
        return [self._extern_arg.name]

    def extern_declarations(self):
        return [self._extern_arg.declaration()]

    def intern_declarations(self):
        if self._intern_var:
            return [self._intern_var.declaration()]
        else:
            return []

class HideArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_arg = None
        self._intern_var = \
                pyf.Var(name=arg.name, dtype=arg.dtype, dimension=None)
        self.value = arg.value
        assert self.value is not None

    def intern_name(self):
        return self._intern_var.name

    def extern_arg_list(self):
        return []

    def extern_declarations(self):
        return []

    def intern_declarations(self):
        return [self._intern_var.declaration()]

    def pre_call_code(self):
        return ["%s = (%s)" % (self._intern_var.name, self.value)]


class ArrayArgWrapper(ArgWrapperBase):

    def __init__(self, arg):
        self._orig_arg = arg
        self._extern_args = []
        self._intern_vars = []
        self._dims = arg.dimension
        self._set_extern_args()

    def _set_extern_args(self):
        orig_name = self._orig_arg.name
        for idx, dim in enumerate(self._dims):
            self._extern_args.append(pyf.Argument(name='%s_d%d' % (orig_name, idx+1),
                                              dtype=pyf.default_integer,
                                              intent='in'))
        dims = [dim.name for dim in self._extern_args]
        self._extern_args.append(pyf.Argument(name=orig_name, dtype=self._orig_arg.dtype,
                                          intent=self._orig_arg.intent,
                                          dimension=dims))

    def extern_declarations(self):
        return [arg.declaration() for arg in self._extern_args]

    def intern_name(self):
        return self._extern_args[-1].name

    def extern_arg_list(self):
        return [arg.name for arg in self._extern_args]

class LogicalWrapper(ArgWrapper):

    def __init__(self, arg):
        super(LogicalWrapper, self).__init__(arg)
        dt = pyf.default_integer
        self._extern_arg = pyf.Argument(name=arg.name, dtype=dt, intent=arg.intent, is_return_arg=arg.is_return_arg)
        self._intern_var = pyf.Var(name=arg.name+'_tmp', dtype=arg.dtype)

    def pre_call_code(self):
        pcc = '''\
if(%(extern_arg)s .ne. 0) then
    %(intern_var)s = .true.
else
    %(intern_var)s = .false.
end if
''' % {'extern_arg' : self._extern_arg.name,
       'intern_var' : self._intern_var.name}

        return pcc.splitlines()

    def post_call_code(self):
        pcc = '''\
if(%(intern_var)s) then
    %(extern_arg)s = 1
else
    %(extern_arg)s = 0
end if
''' % {'extern_arg' : self._extern_arg.name,
       'intern_var' : self._intern_var.name}
        return pcc.splitlines()

