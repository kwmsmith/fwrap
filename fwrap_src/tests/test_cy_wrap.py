from fwrap_src import cy_wrap
from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from cStringIO import StringIO
from fwrap_src.code import CodeBuffer

from tutils import compare

from nose.tools import ok_, eq_, set_trace

class test_empty_func(object):

    def setup(self):
        self.empty_func = pyf.Function(name='empty_func',
                            args=(),
                            return_type=pyf.default_integer)
        self.buf = StringIO()

    def test_empty_func_pyx_wrapper(self):
        cy_wrap.generate_pyx([self.empty_func], self.buf)
        pyx_wrapper = '''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func():
    return DP_c.empty_func_c()
'''.splitlines()
        eq_(pyx_wrapper, self.buf.getvalue().splitlines())
    

    def test_empty_func_pxd_wrapper(self):
        cy_wrap.generate_pxd([self.empty_func], self.buf)
        pxd_wrapper = '''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func()
'''.splitlines()
        eq_(pxd_wrapper, self.buf.getvalue().splitlines())

def make_caws(dts, names, intents=None):
    if intents is None:
        intents = ('in',)*len(dts)
    caws = []
    for dt, name, intent in zip(dts, names, intents):
        arg = pyf.Argument(
                    name,
                    dtype=getattr(pyf, dt),
                    intent=intent)
        fc_arg = fc_wrap.ArgWrapper(arg)
        caws.append(cy_wrap.CyArgWrapper(fc_arg))
    return caws

class test_cy_arg_intents(object):

    def setup(self):
        self.dts = ('default_integer', 'default_real', 'default_logical')
        self.intents = ('in', 'out', 'inout')
        self.caws = make_caws(self.dts, ['name']*len(self.dts), self.intents)
        self.intent_in, self.intent_out, self.intent_inout = self.caws

    def test_pre_call_code(self):
        eq_(self.intent_in.pre_call_code(), [])
        eq_(self.intent_inout.pre_call_code(), [])
        eq_(self.intent_out.pre_call_code(), [])

    def test_post_call_code(self):
        eq_(self.intent_in.post_call_code(), [])
        eq_(self.intent_out.post_call_code(), [])
        eq_(self.intent_inout.post_call_code(), [])

    def test_call_arg_list(self):
        eq_(self.intent_in.call_arg_list(), ['&name'])
        eq_(self.intent_inout.call_arg_list(), ['&name'])
        eq_(self.intent_out.call_arg_list(), ['&name'])

    def test_extern_declarations(self):
        eq_(self.intent_in.extern_declarations(), ['fwrap_default_integer name'])
        eq_(self.intent_inout.extern_declarations(), ['fwrap_default_logical name'])
        eq_(self.intent_out.extern_declarations(), [])

    def test_intern_declarations(self):
        eq_(self.intent_in.intern_declarations(), [])
        eq_(self.intent_inout.intern_declarations(), [])
        eq_(self.intent_out.intern_declarations(), ['cdef fwrap_default_real name'])

    def test_return_tuple_list(self):
        eq_(self.intent_in.return_tuple_list(), [])
        eq_(self.intent_inout.return_tuple_list(), ['name'])
        eq_(self.intent_out.return_tuple_list(), ['name'])

class test_cy_mgr_intents(object):

    def setup(self):
        self.dts = ('default_integer', 'default_real', 'default_logical')
        self.intents = ('in', 'out', 'inout')
        names = ['name'+str(i) for i in range(3)]
        self.caws = make_caws(self.dts, names, self.intents)
        self.mgr = cy_wrap.CyArgWrapperManager(args=self.caws,
                                    return_type_name='fwrap_default_integer')

    def test_arg_declarations(self):
        eq_(self.mgr.arg_declarations(), ['fwrap_default_integer name0',
                                          'fwrap_default_logical name2'])

    def test_intern_declarations(self):
        eq_(self.mgr.intern_declarations(), ['cdef fwrap_default_real name1'])

    def test_return_tuple_list(self):
        eq_(self.mgr.return_tuple_list(), ['name1', 'name2'])

class test_cy_arg_wrapper(object):

    def setup(self):
        self.dts = ('default_integer', 'default_real')
        self.caws = make_caws(self.dts, ['foo']*len(self.dts))

    def test_extern_declarations(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.extern_declarations(), ["fwrap_%s foo" % dt])

    def test_intern_declarations(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.intern_declarations(), [])

    def test_intern_name(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.intern_name(), "foo")

class test_cy_array_arg_wrapper(object):
    
    def setup(self):
        arg1 = pyf.Argument('array', dtype=pyf.default_real,
                            dimension=[':']*3, intent='in')
        arg2 = pyf.Argument('int_array', dtype=pyf.default_integer,
                            dimension=[':']*1, intent='in')
        fc_arg = fc_wrap.ArrayArgWrapper(arg1)
        self.cy_arg = cy_wrap.CyArrayArgWrapper(fc_arg)
        self.cy_int_arg = cy_wrap.CyArrayArgWrapper(fc_wrap.ArrayArgWrapper(arg2))

    def test_extern_declarations(self):
        eq_(self.cy_arg.extern_declarations(), ['object array'])
        eq_(self.cy_int_arg.extern_declarations(), ['object int_array'])

    def test_intern_declarations(self):
        eq_(self.cy_arg.intern_declarations(),
                ["cdef np.ndarray[fwrap_default_real, ndim=3, mode='fortran'] array_ = array",])
        eq_(self.cy_int_arg.intern_declarations(),
                ["cdef np.ndarray[fwrap_default_integer, ndim=1, mode='fortran'] int_array_ = int_array",])

    def test_call_arg_list(self):
        eq_(self.cy_arg.call_arg_list(),
                ['&array_.shape[2]',
                 '&array_.shape[1]',
                 '&array_.shape[0]',
                 '<fwrap_default_real*>array_.data'])
        eq_(self.cy_int_arg.call_arg_list(),
                 ['&int_array_.shape[0]',
                 '<fwrap_default_integer*>int_array_.data'])

class test_cmplx_args(object):

    def setup(self):
        self.intents = ('in', 'out', 'inout', None)
        self.dts = ('default_complex',)*len(self.intents)
        self.caws = make_caws(self.dts, ['name']*len(self.intents), self.intents)
        self.intent_in, self.intent_out, self.intent_inout, \
                self.intent_none = self.caws

    def test_extern_declarations(self):
        eq_(self.intent_in.extern_declarations(),
                ['cy_fwrap_default_complex name'])
        eq_(self.intent_inout.extern_declarations(),
                ['cy_fwrap_default_complex name'])
        eq_(self.intent_none.extern_declarations(),
                ['cy_fwrap_default_complex name'])

    def test_intern_declarations(self):
        eq_(self.intent_out.intern_declarations(),
                ['cdef cy_fwrap_default_complex name',
                 'cdef fwrap_default_complex fw_name'])
        eq_(self.intent_in.intern_declarations(),
                ['cdef fwrap_default_complex fw_name'])
        eq_(self.intent_inout.intern_declarations(),
                ['cdef fwrap_default_complex fw_name'])
        eq_(self.intent_none.intern_declarations(),
                ['cdef fwrap_default_complex fw_name'])

    def test_pre_call_code(self):
        eq_(self.intent_in.pre_call_code(),
                ['CyComplex2fwrap_default_complex(name, fw_name)'])
        eq_(self.intent_out.pre_call_code(),
                [])

    def test_post_call_code(self):
        eq_(self.intent_out.post_call_code(),
                ['fwrap_default_complex2CyComplex(fw_name, name)'])
        eq_(self.intent_in.post_call_code(),
                [])

    def test_call_arg_list(self):
        eq_(self.intent_in.call_arg_list(), ['&fw_name'])
        eq_(self.intent_out.call_arg_list(), ['&fw_name'])
        eq_(self.intent_none.call_arg_list(), ['&fw_name'])

    def test_return_tuple_list(self):
        eq_(self.intent_inout.return_tuple_list(), ['name'])
        eq_(self.intent_out.return_tuple_list(), ['name'])
        eq_(self.intent_in.return_tuple_list(), [])

class test_cy_arg_wrapper_mgr(object):

    def setup(self):
        self.dts = ("default_integer", "default_real")
        self.cy_args = []
        for dt in self.dts:
            arg = pyf.Argument('foo_%s' % dt,
                    dtype=getattr(pyf, dt),
                    intent='in')
            fwarg = fc_wrap.ArgWrapper(arg)
            self.cy_args.append(cy_wrap.CyArgWrapper(fwarg))
        self.rtn = "fwrap_default_integer"
        self.mgr = cy_wrap.CyArgWrapperManager(
                        args=self.cy_args,
                        return_type_name=self.rtn)

    def test_arg_declarations(self):
        eq_(self.mgr.arg_declarations(),
            [cy_arg.extern_declarations()[0] for cy_arg in self.cy_args])

    def test_call_arg_list(self):
        eq_(self.mgr.call_arg_list(),
                ["&%s" % cy_arg.intern_name() for cy_arg in self.cy_args])

    def test_return_arg_declaration(self):
        eq_(self.mgr.return_arg_declaration(),
                ["cdef %s fwrap_return_var" % self.rtn])

class test_cy_proc_wrapper(object):

    def setup(self):
        int_arg_in = pyf.Argument("int_arg_in", pyf.default_integer, 'in')
        int_arg_inout = pyf.Argument("int_arg_inout", pyf.default_integer, 'inout')
        int_arg_out = pyf.Argument("int_arg_out", pyf.default_integer, 'out')
        real_arg = pyf.Argument("real_arg", pyf.default_real)
        all_args = [int_arg_in, int_arg_inout, int_arg_out, real_arg]

        pyf_func = pyf.Function(
                                name="fort_func",
                                args=all_args,
                                return_type=pyf.default_integer)
        func_wrapper = fc_wrap.FunctionWrapper(
                                wrapped=pyf_func)
        self.cy_func_wrapper = cy_wrap.ProcWrapper(
                                wrapped=func_wrapper)

        pyf_subr = pyf.Subroutine(
                            name="fort_subr",
                            args=all_args)
        subr_wrapper = fc_wrap.SubroutineWrapper(
                            wrapped=pyf_subr)
        self.cy_subr_wrapper = cy_wrap.ProcWrapper(
                            wrapped=subr_wrapper)

    def test_func_proc_declaration(self):
        eq_(self.cy_func_wrapper.proc_declaration(),
            'cpdef api object'
            ' fort_func(fwrap_default_integer int_arg_in,'
            ' fwrap_default_integer int_arg_inout,'
            ' fwrap_default_real real_arg):')

    def test_subr_proc_declaration(self):
        eq_(self.cy_subr_wrapper.proc_declaration(),
            'cpdef api object'
            ' fort_subr(fwrap_default_integer int_arg_in,'
            ' fwrap_default_integer int_arg_inout,'
            ' fwrap_default_real real_arg):')

    def test_subr_call(self):
        eq_(self.cy_subr_wrapper.proc_call(),
                'fort_subr_c(&int_arg_in,'
                ' &int_arg_inout, &int_arg_out,'
                ' &real_arg)')

    def test_func_call(self):
        eq_(self.cy_func_wrapper.proc_call(),
                'fwrap_return_var = '
                'fort_func_c(&int_arg_in,'
                ' &int_arg_inout, &int_arg_out,'
                ' &real_arg)')

    def test_subr_declarations(self):
        eq_(self.cy_subr_wrapper.temp_declarations(),
                    ['cdef fwrap_default_integer int_arg_out'])

    def test_func_declarations(self):
        eq_(self.cy_func_wrapper.temp_declarations(),
                    ['cdef fwrap_default_integer int_arg_out',
                     "cdef fwrap_default_integer fwrap_return_var"])

    def test_subr_generate_wrapper(self):
        buf = CodeBuffer()
        self.cy_subr_wrapper.generate_wrapper(buf)
        cy_wrapper = '''\
        cpdef api object fort_subr(fwrap_default_integer int_arg_in, fwrap_default_integer int_arg_inout, fwrap_default_real real_arg):
            cdef fwrap_default_integer int_arg_out
            fort_subr_c(&int_arg_in, &int_arg_inout, &int_arg_out, &real_arg)
            return (int_arg_inout, int_arg_out, real_arg,)
'''
        compare(cy_wrapper, buf.getvalue())

    def test_func_generate_wrapper(self):
        buf = CodeBuffer()
        self.cy_func_wrapper.generate_wrapper(buf)
        cy_wrapper = '''\
        cpdef api object fort_func(fwrap_default_integer int_arg_in, fwrap_default_integer int_arg_inout, fwrap_default_real real_arg):
            cdef fwrap_default_integer int_arg_out
            cdef fwrap_default_integer fwrap_return_var
            fwrap_return_var = fort_func_c(&int_arg_in, &int_arg_inout, &int_arg_out, &real_arg)
            return (fwrap_return_var, int_arg_inout, int_arg_out, real_arg,)
        '''
        compare(cy_wrapper, buf.getvalue())
