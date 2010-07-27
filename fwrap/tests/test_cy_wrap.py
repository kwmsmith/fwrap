from fwrap import cy_wrap
from fwrap import pyf_iface as pyf
from fwrap import fc_wrap
from cStringIO import StringIO
from fwrap.code import CodeBuffer

from tutils import compare

from nose.tools import ok_, eq_, set_trace

def make_caws(dts, names, intents=None):
    if intents is None:
        intents = ('in',)*len(dts)
    caws = []
    for dt, name, intent in zip(dts, names, intents):
        try:
            dtype = getattr(pyf, dt, dt)
        except TypeError:
            dtype = dt
        arg = pyf.Argument(
                    name,
                    dtype=dtype,
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
        eq_(self.intent_in.extern_declarations(),
                ['fwi_integer_t name'])
        eq_(self.intent_inout.extern_declarations(),
                ['fwl_logical_t name'])
        eq_(self.intent_out.extern_declarations(), [])

    def test_intern_declarations(self):
        eq_(self.intent_in.intern_declarations(), [])
        eq_(self.intent_inout.intern_declarations(), [])
        eq_(self.intent_out.intern_declarations(),
                ['cdef fwr_real_t name'])

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
        self.mgr = cy_wrap.CyArgWrapperManager(args=self.caws)

    def test_arg_declarations(self):
        eq_(self.mgr.arg_declarations(), ['fwi_integer_t name0',
                                          'fwl_logical_t name2'])

    def test_intern_declarations(self):
        eq_(self.mgr.intern_declarations(), ['cdef fwr_real_t name1'])

    def test_return_tuple_list(self):
        eq_(self.mgr.return_tuple_list(), ['name1', 'name2'])

class test_cy_arg_wrapper(object):

    def setup(self):
        self.dts = ('default_integer', 'default_real')
        self.caws = make_caws(self.dts, ['foo']*len(self.dts))

    def test_extern_declarations(self):
        extern_decls = ["fwi_integer_t foo", "fwr_real_t foo"]
        for ed, caw in zip(extern_decls, self.caws):
            eq_(caw.extern_declarations(), [ed])

    def test_intern_declarations(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.intern_declarations(), [])

    def test_intern_name(self):
        for dt, caw in zip(self.dts, self.caws):
            eq_(caw.intern_name, "foo")

class test_cy_char_array_arg_wrapper(object):

    def setup(self):
        arg1d = pyf.Argument('charr1',
                            dtype=pyf.CharacterType(
                                fw_ktp='charr_x8', len='20'),
                            dimension=[':'], intent='inout')
        arg2d = pyf.Argument('charr2',
                            dtype=pyf.CharacterType(
                                fw_ktp='charr_x30', len='30'),
                            dimension=[':']*2, intent='inout')
        fc_arg1d = fc_wrap.ArrayArgWrapper(arg1d)
        fc_arg2d = fc_wrap.ArrayArgWrapper(arg2d)
        self.cy_arg1d = cy_wrap.CyCharArrayArgWrapper(fc_arg1d)
        self.cy_arg2d = cy_wrap.CyCharArrayArgWrapper(fc_arg2d)

    def test_intern_declarations(self):
        eq_(self.cy_arg1d.intern_declarations(),
                ["cdef np.ndarray[fw_charr_x8, "
                 "ndim=1, mode='fortran'] charr1_",
                 "cdef fwi_npy_intp charr1_shape[2]"])
        eq_(self.cy_arg2d.intern_declarations(),
                ["cdef np.ndarray[fw_charr_x30, "
                 "ndim=2, mode='fortran'] charr2_",
                 "cdef fwi_npy_intp charr2_shape[3]"])

    def test_pre_call_code(self):
        cmp1 = ["charr1_odtype = charr1.dtype",
                 "for i in range(1): charr1_shape[i+1] = charr1.shape[i]",
                 "charr1.dtype = 'b'",
                 "charr1_ = charr1",
                 "charr1_shape[0] = <fwi_npy_intp>"
                     "(charr1.shape[0]/charr1_shape[1])",]
        eq_(self.cy_arg1d.pre_call_code(), cmp1)
        cmp2 = ["charr2_odtype = charr2.dtype",
                 "for i in range(2): charr2_shape[i+1] = charr2.shape[i]",
                 "charr2.dtype = 'b'",
                 "charr2_ = charr2",
                 "charr2_shape[0] = <fwi_npy_intp>"
                     "(charr2.shape[0]/charr2_shape[1])"]
        eq_(self.cy_arg2d.pre_call_code(), cmp2)

    def test_post_call_code(self):
        eq_(self.cy_arg1d.post_call_code(),
                ["charr1.dtype = charr1_odtype"])
        eq_(self.cy_arg2d.post_call_code(),
                ["charr2.dtype = charr2_odtype"])

    def test_call_arg_list(self):
        eq_(self.cy_arg1d.call_arg_list(),
            ["&charr1_shape[0]",
             "&charr1_shape[1]",
             "<fw_charr_x8*>charr1_.data"])
        eq_(self.cy_arg2d.call_arg_list(),
            ["&charr2_shape[0]",
             "&charr2_shape[1]",
             "&charr2_shape[2]",
             "<fw_charr_x30*>charr2_.data"])

class test_cy_array_arg_wrapper(object):

    def setup(self):
        arg1 = pyf.Argument('array', dtype=pyf.default_real,
                            dimension=[':']*3, intent='in')
        arg2 = pyf.Argument('int_array', dtype=pyf.default_integer,
                            dimension=[':']*1, intent='inout')
        fc_arg = fc_wrap.ArrayArgWrapper(arg1)
        self.cy_arg = cy_wrap.CyArrayArgWrapper(fc_arg)
        self.cy_int_arg = cy_wrap.CyArrayArgWrapper(
                            fc_wrap.ArrayArgWrapper(arg2))

    def test_extern_declarations(self):
        eq_(self.cy_arg.extern_declarations(), ['object array'])
        eq_(self.cy_int_arg.extern_declarations(), ['object int_array'])

    def test_intern_declarations(self):
        eq_(self.cy_arg.intern_declarations(),
                ["cdef np.ndarray[fwr_real_t, "
                 "ndim=3, mode='fortran'] array_",])
        eq_(self.cy_int_arg.intern_declarations(),
                ["cdef np.ndarray[fwi_integer_t, "
                 "ndim=1, mode='fortran'] int_array_",])

    def test_call_arg_list(self):
        eq_(self.cy_arg.call_arg_list(),
                ['<fwi_npy_intp*>&array_.shape[0]',
                 '<fwi_npy_intp*>&array_.shape[1]',
                 '<fwi_npy_intp*>&array_.shape[2]',
                 '<fwr_real_t*>array_.data'])
        eq_(self.cy_int_arg.call_arg_list(),
                 ['<fwi_npy_intp*>&int_array_.shape[0]',
                 '<fwi_integer_t*>int_array_.data'])

    def test_pre_call_code(self):
        eq_(self.cy_arg.pre_call_code(), ["array_ = array",])
        eq_(self.cy_int_arg.pre_call_code(), ["int_array_ = int_array",])

    def test_post_call_code(self):
        eq_(self.cy_arg.post_call_code(), [])
        eq_(self.cy_int_arg.post_call_code(), [])

    def test_return_tuple_list(self):
        eq_(self.cy_arg.return_tuple_list(), [])
        eq_(self.cy_int_arg.return_tuple_list(), ["int_array_"])


class test_char_assumed_size(object):

    def setup(self):
        self.intents = ('in', 'out', 'inout', None)
        self.dtypes = [pyf.CharacterType('ch_xX',
                                        len='*')
                                        for _ in range(4)]
        self.caws = make_caws(self.dtypes,
                              ['name']*len(self.dtypes),
                              self.intents)
        (self.intent_in, self.intent_out,
                self.intent_inout, self.no_intent) = self.caws

    def test_extern_declarations(self):
        eq_(self.intent_out.extern_declarations(),
                ['fw_bytes name'])

    def test_pre_call_code(self):
        eq_(self.intent_out.pre_call_code(),
                ['fw_name_len = len(name)',
                 'fw_name = PyBytes_FromStringAndSize(NULL, fw_name_len)',
                 'fw_name_buf = <char*>fw_name',])
        eq_(self.intent_inout.pre_call_code(),
                ['fw_name_len = len(name)',
                 'fw_name = PyBytes_FromStringAndSize(NULL, fw_name_len)',
                 'fw_name_buf = <char*>fw_name',
                 'memcpy(fw_name_buf, <char*>name, fw_name_len+1)',])

class test_char_args(object):

    def setup(self):
        self.intents = ('in', 'out', 'inout', None)
        self.dtypes = [pyf.CharacterType('ch_%d'%d,
                                        len=str(d)) \
                            for d in (10,20,30,40)]
        self.caws = make_caws(self.dtypes,
                                ['name']*len(self.dtypes),
                                self.intents)
        (self.intent_in, self.intent_out,
                self.intent_inout, self.no_intent) = self.caws

    def test_extern_declarations(self):
        eq_(self.intent_in.extern_declarations(),
               ['fw_bytes name'])
        eq_(self.intent_inout.extern_declarations(),
               ['fw_bytes name'])
        eq_(self.intent_out.extern_declarations(),
               [])

    def test_intern_declarations(self):
        eq_(self.intent_out.intern_declarations(),
                ['cdef fw_bytes fw_name',
                 'cdef fwi_npy_intp fw_name_len',
                 'cdef char *fw_name_buf'])
        eq_(self.intent_in.intern_declarations(),
                ['cdef fw_bytes fw_name',
                 'cdef fwi_npy_intp fw_name_len'])
        eq_(self.intent_inout.intern_declarations(),
                ['cdef fw_bytes fw_name',
                 'cdef fwi_npy_intp fw_name_len',
                 'cdef char *fw_name_buf'])
        eq_(self.no_intent.intern_declarations(),
                ['cdef fw_bytes fw_name',
                 'cdef fwi_npy_intp fw_name_len',
                 'cdef char *fw_name_buf'])

    def test_pre_call_code(self):
        eq_(self.intent_out.pre_call_code(),
                ['fw_name_len = 20',
                 'fw_name = PyBytes_FromStringAndSize(NULL, fw_name_len)',
                 'fw_name_buf = <char*>fw_name'])
        eq_(self.intent_in.pre_call_code(),
                ['fw_name_len = len(name)',
                 'fw_name = name',])
        eq_(self.intent_inout.pre_call_code(),
                ['fw_name_len = 30',
                 'fw_name = PyBytes_FromStringAndSize(NULL, fw_name_len)',
                 'fw_name_buf = <char*>fw_name',
                 'memcpy(fw_name_buf, <char*>name, fw_name_len+1)',])

    def test_post_call_code(self):
        eq_(self.intent_out.post_call_code(), [])
        eq_(self.intent_in.post_call_code(), [])
        eq_(self.intent_inout.post_call_code(), [])

    def test_call_arg_list(self):
        eq_(self.intent_out.call_arg_list(), ['&fw_name_len', 'fw_name_buf'])
        eq_(self.intent_in.call_arg_list(),
                ['&fw_name_len', '<char*>fw_name'])
        eq_(self.intent_inout.call_arg_list(),
                ['&fw_name_len', 'fw_name_buf'])

    def test_return_tuple_list(self):
        eq_(self.intent_inout.return_tuple_list(), ['fw_name'])
        eq_(self.intent_out.return_tuple_list(), ['fw_name'])
        eq_(self.intent_in.return_tuple_list(), [])

class test_cmplx_args(object):

    def setup(self):
        self.intents = ('in', 'out', 'inout', None)
        self.dts = ('default_complex',)*len(self.intents)
        self.caws = make_caws(self.dts,
                              ['name']*len(self.intents),
                              self.intents)
        self.intent_in, self.intent_out, self.intent_inout, \
                self.intent_none = self.caws

    def test_extern_declarations(self):
        eq_(self.intent_in.extern_declarations(),
                ['fwc_complex name'])
        eq_(self.intent_inout.extern_declarations(),
                ['fwc_complex name'])
        eq_(self.intent_none.extern_declarations(),
                ['fwc_complex name'])

    def test_intern_declarations(self):
        eq_(self.intent_out.intern_declarations(),
                ['cdef fwc_complex name'])
        eq_(self.intent_in.intern_declarations(), [])
        eq_(self.intent_inout.intern_declarations(), [])
        eq_(self.intent_none.intern_declarations(), [])

    def test_pre_call_code(self):
        eq_(self.intent_in.pre_call_code(), [])
        eq_(self.intent_out.pre_call_code(), [])

    def test_post_call_code(self):
        eq_(self.intent_out.post_call_code(), [])
        eq_(self.intent_in.post_call_code(), [])

    def test_call_arg_list(self):
        eq_(self.intent_in.call_arg_list(), ['&name'])
        eq_(self.intent_out.call_arg_list(), ['&name'])
        eq_(self.intent_none.call_arg_list(), ['&name'])

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
        self.mgr = cy_wrap.CyArgWrapperManager(args=self.cy_args)

    def test_arg_declarations(self):
        eq_(self.mgr.arg_declarations(),
            [cy_arg.extern_declarations()[0] for cy_arg in self.cy_args])

    def test_call_arg_list(self):
        eq_(self.mgr.call_arg_list(),
                ["&%s" % cy_arg.intern_name for cy_arg in self.cy_args])

class test_empty_ret_tuple(object):

    def test_empty_ret(self):
        int_args_in = [pyf.Argument('a1', pyf.default_integer, 'in'),
                       pyf.Argument('a2', pyf.default_integer, 'in')]
        subr = pyf.Subroutine(name='dummy',
                args=int_args_in)
        fc_wrapper = fc_wrap.SubroutineWrapper(wrapped=subr)
        cy_wrapper = cy_wrap.ProcWrapper(wrapped=fc_wrapper)
        eq_(cy_wrapper.return_tuple(), '')

class test_cy_proc_wrapper(object):

    def setup(self):
        int_arg_in = pyf.Argument("int_arg_in", pyf.default_integer, 'in')
        int_arg_inout = pyf.Argument("int_arg_inout",
                                     pyf.default_integer, 'inout')
        int_arg_out = pyf.Argument("int_arg_out", pyf.default_integer, 'out')
        real_arg = pyf.Argument("real_arg", pyf.default_real)
        all_args = [int_arg_in, int_arg_inout, int_arg_out, real_arg]

        return_arg = pyf.Argument(name="fort_func", dtype=pyf.default_integer)
        pyf_func = pyf.Function(
                                name="fort_func",
                                args=all_args,
                                return_arg=return_arg)
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
            ' fort_func(fwi_integer_t int_arg_in,'
            ' fwi_integer_t int_arg_inout,'
            ' fwr_real_t real_arg):')

    def test_subr_proc_declaration(self):
        eq_(self.cy_subr_wrapper.proc_declaration(),
            'cpdef api object'
            ' fort_subr(fwi_integer_t int_arg_in,'
            ' fwi_integer_t int_arg_inout,'
            ' fwr_real_t real_arg):')

    def test_subr_call(self):
        eq_(self.cy_subr_wrapper.proc_call(),
                'fort_subr_c(&int_arg_in,'
                ' &int_arg_inout, &int_arg_out,'
                ' &real_arg, &fw_iserr__, fw_errstr__)')

    def test_func_call(self):
        eq_(self.cy_func_wrapper.proc_call(), 'fort_func_c'
                                              '(&fw_ret_arg, '
                                              '&int_arg_in, '
                                              '&int_arg_inout, '
                                              '&int_arg_out, '
                                              '&real_arg, '
                                              '&fw_iserr__, '
                                              'fw_errstr__)')

    def test_subr_declarations(self):
        buf = CodeBuffer()
        self.cy_subr_wrapper.temp_declarations(buf)
        compare(buf.getvalue(), 'cdef fwi_integer_t int_arg_out\n'
                                'cdef fwi_integer_t fw_iserr__\n'
                                'cdef fw_character fw_errstr__[fw_errstr_len]')

    def test_func_declarations(self):
        buf = CodeBuffer()
        self.cy_func_wrapper.temp_declarations(buf)
        decls = '''\
        cdef fwi_integer_t fw_ret_arg
        cdef fwi_integer_t int_arg_out
        cdef fwi_integer_t fw_iserr__
        cdef fw_character fw_errstr__[fw_errstr_len]
                '''
        compare(buf.getvalue(), decls)

    def test_subr_generate_wrapper(self):
        buf = CodeBuffer()
        self.cy_subr_wrapper.generate_wrapper(buf)
        cy_wrapper = '''\
        cpdef api object fort_subr(fwi_integer_t int_arg_in, fwi_integer_t int_arg_inout, fwr_real_t real_arg):
            cdef fwi_integer_t int_arg_out
            cdef fwi_integer_t fw_iserr__
            cdef fw_character fw_errstr__[fw_errstr_len]
            fort_subr_c(&int_arg_in, &int_arg_inout, &int_arg_out, &real_arg, &fw_iserr__, fw_errstr__)
            if fw_iserr__ != FW_NO_ERR__:
                raise RuntimeError("an error was encountered when calling the 'fort_subr' wrapper.")
            return (int_arg_inout, int_arg_out, real_arg,)
'''
        compare(cy_wrapper, buf.getvalue())

    def test_func_generate_wrapper(self):
        buf = CodeBuffer()
        self.cy_func_wrapper.generate_wrapper(buf)
        cy_wrapper = '''\
        cpdef api object fort_func(fwi_integer_t int_arg_in, fwi_integer_t int_arg_inout, fwr_real_t real_arg):
            cdef fwi_integer_t fw_ret_arg
            cdef fwi_integer_t int_arg_out
            cdef fwi_integer_t fw_iserr__
            cdef fw_character fw_errstr__[fw_errstr_len]
            fort_func_c(&fw_ret_arg, &int_arg_in, &int_arg_inout, &int_arg_out, &real_arg, &fw_iserr__, fw_errstr__)
            if fw_iserr__ != FW_NO_ERR__:
                raise RuntimeError("an error was encountered when calling the 'fort_func' wrapper.")
            return (fw_ret_arg, int_arg_inout, int_arg_out, real_arg,)
        '''
        compare(cy_wrapper, buf.getvalue())
