from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

from tutils import compare

class test_generation(object):
    
    def setup(self):
        fsrc = StringIO('''\
function empty_func()
    implicit none
    integer :: empty_func
end function empty_func
''')
        self.ast = main.generate_ast(fsrc)
        self.fc_wrap = main.wrap_fc(self.ast)
        self.cy_wrap = main.wrap_cy(self.fc_wrap)
        self.buf = CodeBuffer()

    def test_generate_ast(self):
        empty_func = pyf.Function(name='empty_func',
                        args=(),
                        return_type=pyf.default_integer)
        eq_(self.ast[0].name, empty_func.name)
        eq_(self.ast[0].return_arg.name, empty_func.return_arg.name)
        eq_(self.ast[0]._args, empty_func._args)

    def test_generate_fc(self):
        main.generate_fc_f(self.fc_wrap, self.buf)
        fc = '''\
        function empty_func_c() bind(c, name="empty_func_c")
            use fwrap_ktp_mod
            implicit none
            integer(fwrap_default_integer) :: empty_func_c
            interface
                function empty_func()
                    use fwrap_ktp_mod
                    implicit none
                    integer(fwrap_default_integer) :: empty_func
                end function empty_func
            end interface
            empty_func_c = empty_func()
        end function empty_func_c
        '''
        compare(fc, self.buf.getvalue())

    def test_generate_fc_h(self):
        main.generate_fc_h(self.fc_wrap, self.buf)
        header = '''\
        #include "fwrap_ktp_header.h"

        fwrap_default_integer empty_func_c();
        '''
        compare(self.buf.getvalue(), header)

    def test_generate_pxd_fc(self):
        main.generate_fc_pxd(self.fc_wrap, projname="DP", buf=self.buf)
        header = '''\
        from fwrap_ktp cimport *

        cdef extern from "DP_fc.h":
            fwrap_default_integer empty_func_c()
        '''
        compare(header, self.buf.getvalue())

    def test_generate_cy_pxd(self):
        main.generate_cy_pxd(self.cy_wrap, projname="DP", buf=self.buf)
        pxd = '''\
        from DP_fc cimport *

        cpdef api object empty_func()
        '''
        compare(pxd, self.buf.getvalue())

    def test_generate_cy_pyx(self):
        main.generate_cy_pyx(self.cy_wrap, buf=self.buf)
        buf2 = CodeBuffer()
        self.cy_wrap[0].generate_wrapper(buf2)
        compare(buf2.getvalue(), self.buf.getvalue())

    def test_generate_genconfig(self):
        main.generate_genconfig(self.ast, buf=self.buf)
        ok_(genconfig_code in self.buf.getvalue(), "'%s' \n\n not in \n\n '%s'" % (genconfig_code, self.buf.getvalue()))

genconfig_code = '''\
program genconfig
    use fc_type_map
    implicit none
    integer :: iserr
    iserr = 0

    call open_map_file(iserr)
    if (iserr .ne. 0) then
        print *, errmsg
        stop 1
    endif
    call lookup_integer(kind(0), "fwrap_default_integer", iserr)
    if (iserr .ne. 0) then
        goto 100
    endif
    goto 200
    100 print *, errmsg
    call close_map_file(iserr)
    stop 1
    200 call close_map_file(iserr)
end program genconfig'''
