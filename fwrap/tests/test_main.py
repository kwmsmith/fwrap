import os
import tempfile

from fwrap import fc_wrap
from fwrap import cy_wrap
from fwrap import constants
from fwrap import main
from cStringIO import StringIO
from fwrap import pyf_iface as pyf
from fwrap.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

from tutils import compare

class test_main(object):

    fsrc = '''\
function empty_func()
    implicit none
    integer :: empty_func
    empty_func = 1
end function empty_func
'''

    def setup(self):
        self.name = 'test'
        self.source_file_lst = [self.fsrc]
        



    def test_parse(self):
        ast = main.parse(self.source_file_lst)
        return_arg = pyf.Argument('empty_func', dtype=pyf.default_integer)
        empty_func = pyf.Function(name='empty_func',
                                  args=(),
                                  return_arg=return_arg)
        eq_(ast[0].name, empty_func.name)
        eq_(ast[0].return_arg.name, empty_func.return_arg.name)
        eq_(len(ast[0].args), len(empty_func.args))

    def test_generate_fc_f(self):
        fort_ast = main.parse(self.source_file_lst)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        fname, buf = main.generate_fc_f(c_ast, self.name)
        fc = '''\
        subroutine empty_func_c(fw_ret_arg, fw_iserr__, fw_errstr__) bind(c, name="em&
        &pty_func_c")
            use fwrap_ktp_mod
            implicit none
            integer(kind=fwrap_default_integer), intent(out) :: fw_ret_arg
            integer(kind=fwrap_default_integer), intent(out) :: fw_iserr__
            character(kind=fwrap_default_character, len=1), dimension(FW_ERRSTR_LEN) &
        &:: fw_errstr__
            interface
                function empty_func()
                    use fwrap_ktp_mod
                    implicit none
                    integer(kind=fwrap_default_integer) :: empty_func
                end function empty_func
            end interface
            fw_iserr__ = FW_INIT_ERR__
            fw_ret_arg = empty_func()
            fw_iserr__ = FW_NO_ERR__
        end subroutine empty_func_c
        '''
        compare(fc, buf.getvalue())

    def test_generate_fc_h(self):
        fort_ast = main.parse(self.source_file_lst)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        fname, buf = main.generate_fc_h(c_ast, self.name)
        header = '''\
        #include "fwrap_ktp_header.h"

        void empty_func_c(fwrap_default_integer *fw_ret_arg, fwrap_default_integer *fw_iserr__, fwrap_default_character *fw_errstr__);
        '''
        compare(buf.getvalue(), header)
        eq_(fname, constants.FC_HDR_TMPL % self.name)

    def test_generate_fc_pxd(self):
        fort_ast = main.parse(self.source_file_lst)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        fname, buf = main.generate_fc_pxd(c_ast, self.name)
        header = '''\
        from fwrap_ktp cimport *

        cdef extern from "test_fc.h":
            void empty_func_c(fwrap_default_integer *fw_ret_arg, fwrap_default_integer *fw_iserr__, fwrap_default_character *fw_errstr__)
        '''
        compare(header, buf.getvalue())

    def test_generate_cy_pxd(self):
        fort_ast = main.parse(self.source_file_lst)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        cython_ast = cy_wrap.wrap_fc(c_ast)
        fname, buf = main.generate_cy_pxd(cython_ast, self.name)
        pxd = '''\
        cimport numpy as np
        from test_fc cimport *

        cpdef api object empty_func()
        '''
        compare(pxd, buf.getvalue())

    def test_generate_cy_pyx(self):
        fort_ast = main.parse(self.source_file_lst)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        cython_ast = cy_wrap.wrap_fc(c_ast)
        fname, buf = main.generate_cy_pyx(cython_ast, self.name)
        test_str = '''\
cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)
cpdef api object empty_func():
    cdef fwrap_default_integer fw_ret_arg
    cdef fwrap_default_integer fw_iserr__
    cdef fwrap_default_character fw_errstr__[FW_ERRSTR_LEN]
    empty_func_c(&fw_ret_arg, &fw_iserr__, fw_errstr__)
    if fw_iserr__ != FW_NO_ERR__:
        raise RuntimeError("an error was encountered when calling the 'empty_func' wrapper.")
    return (fw_ret_arg,)
'''
        compare(test_str, buf.getvalue())

    def test_generate_type_specs(self):
        from cPickle import loads
        fort_ast = main.parse(self.source_file_lst)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        cython_ast = cy_wrap.wrap_fc(c_ast)
        fname, buf = main.generate_type_specs(fort_ast, self.name)
        ctps = loads(buf.getvalue())
        for ctp in ctps:
            ok_(isinstance(ctp, dict))
            eq_(sorted(ctp.keys()), 
                    ['basetype', 'fwrap_name', 'lang', 'odecl'])
