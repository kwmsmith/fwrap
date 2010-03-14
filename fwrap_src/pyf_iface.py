class Dtype(object):

    def type_spec(self):
        return '%s(%s)' % (self.type, self.ktp)

class IntegerType(Dtype):

    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'integer'

default_integer = IntegerType(ktp='fwrap_default_int')

class LogicalType(Dtype):

    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'logical'

default_logical = LogicalType(ktp='fwrap_default_logical')

class RealType(Dtype):

    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'real'

default_real = RealType(ktp='fwrap_default_real')
default_dbl  = RealType(ktp='fwrap_default_double')

class ComplexType(Dtype):

    def __init__(self, ktp):
        self.ktp = ktp
        self.type = 'complex'

default_complex = ComplexType(ktp='fwrap_default_complex')
default_double_complex = ComplexType(ktp='fwrap_default_dbl_cmplx')

class Parameter(object):
    
    def __init__(self, name, dtype, value):
        self.name = name
        self.dtype = dtype
        self.value = value


class Var(object):
    def __init__(self, name, dtype, dimension=None):
        self.name = name
        self.dtype = dtype
        self.dimension = dimension
        if self.dimension:
            self.is_array = True
        else:
            self.is_array = False

    def var_specs(self):
        specs = [self.dtype.type_spec()]
        if self.dimension:
            specs.append('dimension(%s)' % ', '.join(self.dimension))
        return specs

    def declaration(self):
        return '%s :: %s' % (', '.join(self.var_specs()), self.name)


class Argument(object):

    def __init__(self, name, dtype,
                 intent=None,
                 dimension=None,
                 value=None,
                 is_return_arg=False):
        self._var = Var(name=name, dtype=dtype, dimension=dimension)
        self.intent = intent
        self.value = value
        self.is_return_arg = is_return_arg

    def _get_name(self):
        return self._var.name
    name = property(_get_name)

    def _get_dtype(self):
        return self._var.dtype
    dtype = property(_get_dtype)

    def _get_dimension(self):
        return self._var.dimension
    dimension = property(_get_dimension)

    def _is_array(self):
        return self._var.is_array
    is_array = property(_is_array)

    def declaration(self):
        var = self._var
        specs = var.var_specs()
        if self.intent and not self.is_return_arg:
            if self.intent != 'hide':
                specs.append('intent(%s)' % self.intent)
        return '%s :: %s' % (', '.join(specs), self.name)

class ProcArgument(object):
    def __init__(self, proc):
        self.proc = proc
        self.name = proc.name

class ArgManager(object):
    
    def __init__(self, args, return_arg=None):
        self._args = args
        self._return_arg = return_arg

    def extern_arg_list(self):
        ret = []
        for arg in self._args:
            ret.append(arg.name)
        return ret

    def order_declarations(self):
        decl_list = []
        undeclared = self._args[:]
        while undeclared:
            for arg in undeclared[:]:
                if not arg.is_array:
                    decl_list.append(arg)
                    undeclared.remove(arg)
                else:
                    shape_declared = True
                    undecl_names = [_arg.name for _arg in undeclared]
                    for ext_name in arg.dimension:
                        if ext_name in undecl_names:
                            shape_declared = False
                            break
                    if shape_declared:
                        decl_list.append(arg)
                        undeclared.remove(arg)
        assert not undeclared
        assert len(decl_list) == len(self._args)
        return decl_list

    def arg_declarations(self):
        decls = []
        for arg in self.order_declarations():
            decls.append(arg.declaration())
        if self._return_arg:
            decls.append(self._return_arg.declaration())
        return decls

    def return_var_name(self):
        return self._return_arg.name

class Procedure(object):

    def __init__(self, name, args):
        super(Procedure, self).__init__()
        self.name = name
        self._args = args
        self.arg_man = None

    def extern_arg_list(self):
        return self.arg_man.extern_arg_list()

    def arg_declarations(self):
        return self.arg_man.arg_declarations()

    def procedure_decl(self):
        return "%s %s(%s)" % (self.kind, self.name, ', '.join(self.extern_arg_list()))

    def proc_preamble(self, buf):
        buf.putln('use config')
        buf.putln('implicit none')
        for decl in self.arg_declarations():
            buf.putln(decl)

    def procedure_end(self):
        return "end %s %s" % (self.kind, self.name)

    def generate_interface(self, buf):
        buf.putln('interface')
        buf.indent()
        buf.putln(self.procedure_decl())
        buf.indent()
        self.proc_preamble(buf)
        buf.dedent()
        buf.putln(self.procedure_end())
        buf.dedent()
        buf.putln('end interface')


class Function(Procedure):
    
    def __init__(self, name, args, return_type):
        super(Function, self).__init__(name, args)
        self.return_arg = Argument(name=name, dtype=return_type, intent='out', is_return_arg=True)
        self.kind = 'function'
        self.arg_man = ArgManager(self._args, self.return_arg)

class Subroutine(Procedure):

    def __init__(self, name, args):
        super(Subroutine, self).__init__(name, args)
        self.kind = 'subroutine'
        self.arg_man = ArgManager(self._args)

class Module(object):

    def __init__(self, name, mod_objects=None, uses=None):
        pass

class Use(object):

    def __init__(self, mod, only=None):
        pass
