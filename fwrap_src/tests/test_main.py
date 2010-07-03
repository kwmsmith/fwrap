import tempfile

from fwrap_src import constants
from fwrap_src import main
from cStringIO import StringIO
from fwrap_src import pyf_iface as pyf
from fwrap_src.code import CodeBuffer

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
        self.build_dir = tempfile.mkdtemp()
        self.source_file = os.path.join(build_dir,'source.f90')
        file = open(self.source_file,'w')
        file.write(fsrc)
        file.close()
        self.name = 'test'
        
    def test_parse(self):
        ast = main.parse(self.source_file)
        empty_func = pyf.Function(name='empty_func',
                                  args=(),
                                  return_type=pyf.default_integer)
        eq_(ast[0].name, empty_func.name)
        eq_(ast[0].return_arg.name, empty_func.return_arg.name)
        eq_(len(ast[0].args), len(empty_func.args))
        
    # def test_generate(self):
    #     ast = main.parse(self.source_file)
    #     generate(ast,self.name,self.build_dir)

    def test_generate_fc_f(self):
        fort_ast = main.parse(self.source_file)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        fname, buf = main.generate_fc_f(c_ast, self.name)
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
        fort_ast = main.parse(self.source_file)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        fname, buf = main.generate_fc_h(c_ast, self.name)
        header = '''\
        #include "fwrap_ktp_header.h"
    
        fwrap_default_integer empty_func_c();
        '''
        compare(buf.getvalue(), header)
        eq_(fname, constants.FC_HDR_TMPL % self.name)

    def test_generate_fc_pxd(self):
        fort_ast = main.parse(self.source_file)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        fname, buf = main.generate_fc_pxd(c_ast, self.name)
        header = '''\
        from fwrap_ktp cimport *
    
        cdef extern from "DP_fc.h":
            fwrap_default_integer empty_func_c()
        '''
        compare(header, buf.getvalue())

    def test_generate_cy_pxd(self):
        fort_ast = main.parse(self.source_file)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        cython_ast = cy_wrap.wrap_fc(fort_ast)
        fname, buf = main.generate_cy_pxd(cython_ast, self.name)
        pxd = '''\
        cimport numpy as np
        from DP_fc cimport *
    
        cpdef api object empty_func()
        '''
        compare(pxd, buf.getvalue())

    def test_generate_cy_pyx(self):
        fort_ast = main.parse(self.source_file)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        cython_ast = cy_wrap.wrap_fc(fort_ast)
        fname, buf = main.generate_cy_pyx(cython_ast, self.name)
        buf2 = CodeBuffer()
        self.cython_ast[0].generate_wrapper(buf2)
        compare(buf2.getvalue(), buf.getvalue())

    def test_generate_type_specs(self):
        from cPickle import loads
        fort_ast = main.parse(self.source_file)
        c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
        cython_ast = cy_wrap.wrap_fc(fort_ast)
        fname, buf = main.generate_type_specs(fort_ast, self.name)
        ctps = loads(buf.getvalue())
        for ctp in ctps:
            ok_(isinstance(ctp, dict))
            eq_(sorted(ctp.keys()), ['basetype', 'fwrap_name', 'lang', 'odecl'])
            
    def teardown(self):
        os.removedirs(self.build_dir)
