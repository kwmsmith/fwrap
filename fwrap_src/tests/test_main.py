from fwrap_src import constants
from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

from tutils import compare

class fake_options(object):
    pass

class test_reflow(object):

    def test_reflow(self):
        fsrc = '''\
subroutine many_args(a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a20, a21, a22,&
a23, a24, a25, a26, a27, a28, a29, a30, a31, a32, a33, a34, a35, a36, a37,&
a38, a39, a40, a41, a42, a43, a44, a45, a46, a47, a48, a49)
    implicit none
    integer, intent(in) :: a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a20, a21, a22,&
    a23, a24, a25, a26, a27, a28, a29, a30, a31, a32, a33, a34, a35, a36, a37,&
    a38, a39, a40, a41, a42, a43, a44, a45, a46, a47, a48, a49
end subroutine many_args
'''
        ast = main.generate_ast([fsrc])
        fc_wrap = main.wrap_fc(ast)
        options = fake_options()
        options.projectname = 'DP'

        fname, buf = main.generate_fc_f(fc_wrap, options)
        for line in buf.getvalue().splitlines():
            ok_(len(line) <= 79, "len('%s') > 79" % line)

class test_generation(object):

    def setup(self):
        fsrc = '''\
function empty_func()
    implicit none
    integer :: empty_func
    empty_func = 1
end function empty_func
'''
        self.ast = main.generate_ast([fsrc])
        self.fc_wrap = main.wrap_fc(self.ast)
        self.cy_wrap = main.wrap_cy(self.fc_wrap)
        self.options = fake_options()
        self.options.projectname = "DP"

    def test_generate_ast(self):
        empty_func = pyf.Function(name='empty_func',
                        args=(),
                        return_type=pyf.default_integer)
        eq_(self.ast[0].name, empty_func.name)
        eq_(self.ast[0].return_arg.name, empty_func.return_arg.name)
        eq_(len(self.ast[0].args), len(empty_func.args))

    def test_generate_fc_f(self):
        fname, buf = main.generate_fc_f(self.fc_wrap, self.options)
        fc = '''\
        function empty_func_c() bind(c, name="empty_func_c")
            use fwrap_ktp_mod
            implicit none
            integer(kind=fwrap_default_integer) :: empty_func_c
            interface
                function empty_func()
                    use fwrap_ktp_mod
                    implicit none
                    integer(kind=fwrap_default_integer) :: empty_func
                end function empty_func
            end interface
            empty_func_c = empty_func()
        end function empty_func_c
        '''
        compare(fc, buf.getvalue())

    def test_generate_fc_h(self):
        fname, buf = main.generate_fc_h(self.fc_wrap, self.options)
        header = '''\
        #include "fwrap_ktp_header.h"

        fwrap_default_integer empty_func_c();
        '''
        compare(buf.getvalue(), header)
        eq_(fname, constants.FC_HDR_TMPL % self.options.projectname)

    def test_generate_fc_pxd(self):
        fname, buf = main.generate_fc_pxd(self.fc_wrap, self.options)
        header = '''\
        from fwrap_ktp cimport *

        cdef extern from "DP_fc.h":
            fwrap_default_integer empty_func_c()
        '''
        compare(header, buf.getvalue())

    def test_generate_cy_pxd(self):
        fname, buf = main.generate_cy_pxd(self.cy_wrap, self.options)
        pxd = '''\
        cimport numpy as np
        from DP_fc cimport *

        cpdef api object empty_func()
        '''
        compare(pxd, buf.getvalue())

    def test_generate_cy_pyx(self):
        fname, buf = main.generate_cy_pyx(self.cy_wrap, self.options)
        test_str = '''\
cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)
cpdef api object empty_func():
    cdef fwrap_default_integer fwrap_return_var
    fwrap_return_var = empty_func_c()
    return (fwrap_return_var,)
'''
        compare(test_str, buf.getvalue())

    def test_generate_type_specs(self):
        from cPickle import loads
        fname, buf = main.generate_type_specs(self.ast, self.options)
        ctps = loads(buf.getvalue())
        for ctp in ctps:
            ok_(isinstance(ctp, dict))
            eq_(sorted(ctp.keys()), ['basetype', 'fwrap_name', 'lang', 'odecl'])
