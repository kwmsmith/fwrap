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
        fc_wrap.GenFortran(pname).generate([self.empty_func], self.buf)
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
        fc_wrap.GenCHeader(pname).generate([self.empty_func], self.buf)
        header_file = '''
#include "config.h"
fwrap_default_int empty_func_c();
'''.splitlines()
        eq_(header_file, self.buf.getvalue().splitlines())

    def test_generate_pxd_empty_func(self):
        pname = "DP"
        fc_wrap.GenPxd(pname).generate([self.empty_func], self.buf)
        pxd_file = '''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''.splitlines()
        eq_(pxd_file, self.buf.getvalue().splitlines())

class Mock(object):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

def _test_gen_fortran_one_arg_func():
    pname = "FB"
    one_arg = Mock(name='one_arg',
                   args=[Mock(name='a',
                              dtype=Mock(type='integer', ktp='fwrap_default_int'),
                              intent="in")],
                   return_type=Mock(type='integer', ktp='fwrap_default_int'))
    buf = StringIO()
    fc_wrap.GenFortran(pname).generate([one_arg], buf)
    fort_file = '''
function fw_one_arg(a) bind(c, name="one_arg_c")
    use config
    implicit none
    integer(fwrap_default_int), intent(in) :: a
    integer(fwrap_default_int) :: fw_one_arg
    interface
        function one_arg(a)
            implicit none
            integer, intent(in) :: a
            integer :: empty_func
        end function one_arg
    end interface
    fw_one_arg = one_arg(a)
end function fw_one_arg
'''.splitlines()
    eq_(fort_file, buf.getvalue().splitlines())

def test_get_filenames():
    projname = "DP"
    ofs = [(fc_wrap.GenFortran(projname), "DP_c.f90"),
           (fc_wrap.GenCHeader(projname), "DP_c.h"),
           (fc_wrap.GenPxd(projname), "DP_c.pxd")]
    for obj, fname in ofs:
        eq_(obj.filename, fname)

def test_generate_empty_func_interface():
    empty_func = Mock(name='empty_func',
                      args=(),
                      return_type=Mock(type='integer', ktp='fwrap_default_int'))
    buf = StringIO()
    fc_wrap.GenFortran("DP").generate_interface(empty_func, buf)
    iface = '''
interface
    function empty_func()
        use config
        implicit none
        integer(fwrap_default_int) :: empty_func
    end function empty_func
end interface
'''.splitlines()
    eq_(iface, buf.getvalue().splitlines())

def test_generate_one_arg_func_iface():
    one_arg_func = Mock(name='one_arg_func',
                      args=[Mock(name='arg1',
                                dtype=Mock(type='real', ktp='fwrap_default_real'),
                                intent='inout')],
                      return_type=Mock(type='integer', ktp='fwrap_default_int'))
    buf = StringIO()
    fc_wrap.GenFortran("DP").generate_interface(one_arg_func, buf)
    iface = '''
interface
    function one_arg_func(a)
        use config
        implicit none
        real(fwrap_default_real), intent(inout) :: a
        integer(fwrap_default_int) :: one_arg_func
    end function one_arg_func
end interface
'''.splitlines()
    eq_(iface, buf.getvalue().splitlines())
