from fwrap_src import constants
from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

from tutils import compare

class test_generation(object):

    class fake_options(object):
        pass
    
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
        self.options = test_generation.fake_options()
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
        from DP_fc cimport *

        cpdef api object empty_func()
        '''
        compare(pxd, buf.getvalue())

    def test_generate_cy_pyx(self):
        fname, buf = main.generate_cy_pyx(self.cy_wrap, self.options)
        buf2 = CodeBuffer()
        self.cy_wrap[0].generate_wrapper(buf2)
        compare(buf2.getvalue(), buf.getvalue())

    def test_generate_type_specs(self):
        from cPickle import loads
        fname, buf = main.generate_type_specs(self.ast, self.options)
        ctps = loads(buf.getvalue())
        for ctp in ctps:
            ok_(isinstance(ctp, dict))
            eq_(sorted(ctp.keys()), ['basetype', 'fwrap_name', 'type_decl'])
        

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
