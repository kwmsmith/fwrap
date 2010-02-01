from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from cStringIO import StringIO

from nose.tools import ok_, eq_, set_trace

class test_empty_func(object):

    def setup(self):
        self.empty_func = pyf.function(name='empty_func',
                        args=(),
                        return_type=pyf.default_integer)
        self.buf = StringIO()

    def teardown(self):
        del self.empty_func
        del self.buf

    def test_generate_fortran_empty_func(self):
        pname = "DP"
        fc_wrap.FCWrapFortran(pname).generate([self.empty_func], self.buf)
        fort_file = '''
function fw_empty_func() bind(c, name="empty_func_c")
    use iso_c_binding
    implicit none
    integer(c_int) :: fw_empty_func
    interface
        function empty_func()
            implicit none
            integer :: empty_func
        end function empty_func
    end interface
    fw_empty_func = empty_func()
end function fw_empty_func
'''.splitlines()
        eq_(fort_file, self.buf.getvalue().splitlines())

    def test_generate_header_empty_func(self):
        pname = "DP"
        fc_wrap.FCWrapCHeader(pname).generate([self.empty_func], self.buf)
        header_file = '''
#include "config.h"
fwrap_default_int empty_func_c();
'''.splitlines()
        eq_(header_file, self.buf.getvalue().splitlines())

    def test_generate_pxd_empty_func(self):
        pname = "DP"
        fc_wrap.FCWrapPxd(pname).generate([self.empty_func], self.buf)
        pxd_file = '''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''.splitlines()
        eq_(pxd_file, self.buf.getvalue().splitlines())

def test_get_filenames():
    projname = "DP"
    ofs = [(fc_wrap.FCWrapFortran(projname), "DP_c.f90"),
           (fc_wrap.FCWrapCHeader(projname), "DP_c.h"),
           (fc_wrap.FCWrapPxd(projname), "DP_c.pxd")]
    for obj, fname in ofs:
        eq_(obj.filename, fname)
