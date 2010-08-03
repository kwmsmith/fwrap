#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Fwrap project nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#------------------------------------------------------------------------------

from fwrap import pyf_iface as pyf

from nose.tools import eq_, ok_

class test_parameter(object):

    def setup(self):
        self.lit_int = pyf.Parameter('int_param',
                dtype=pyf.default_integer, expr="10+20")
        self.var_param = pyf.Parameter("var_param",
                dtype=pyf.default_integer, expr="int_param + 30")
        self.call_func = pyf.Parameter("call_func",
                dtype=pyf.default_integer, expr="selected_int_kind(10)")

    def test_depends(self):
        eq_(self.lit_int.depends(), set())
        eq_(self.var_param.depends(), set(["int_param"]))
        eq_(self.call_func.depends(), set([]))

class test_proc_params(object):

    def setup(self):
        self.lit_int = pyf.Parameter("lit_int",
                dtype=pyf.default_integer, expr="30-10")
        self.sik = pyf.Parameter("sik_10",
                dtype=pyf.default_integer, expr="selected_int_kind(10)")
        self.srk = pyf.Parameter(
                        "srk_10_20",
                        dtype=pyf.default_integer,
                        expr="selected_real_kind(10, lit_int)")
        srk_real = pyf.RealType("srk_10_20", kind="srk_10_20")
        self.real_arg = pyf.Argument("real_arg",
                dtype=srk_real, intent='inout')
        sik_int = pyf.IntegerType("sik_10", kind="sik_10")
        self.int_arg = pyf.Argument("int_arg",
                dtype=sik_int, dimension=[("lit_int",)])
        subr = pyf.Subroutine(
                        name="subr",
                        args=[self.real_arg, self.int_arg],
                        params=[self.lit_int, self.sik, self.srk])
        self.ret_arg = pyf.Argument("func", dtype=srk_real)
        func = pyf.Function(
                name="func",
                args=[self.real_arg, self.int_arg],
                params=[self.lit_int, self.sik, self.srk],
                return_arg=self.ret_arg)
        self.args = [self.real_arg, self.int_arg]
        self.params = [self.lit_int, self.sik, self.srk]

    def test_arg_man(self):
        sub_am = pyf.ArgManager(args=self.args, params=self.params)
        func_am = pyf.ArgManager(args=self.args,
                        return_arg=self.ret_arg, params=self.params)
        eq_(sub_am.arg_declarations(),
                ['integer(kind=fwi_integer_t), '
                        'parameter :: lit_int = 30-10',
                 'integer(kind=fwi_integer_t), '
                         'parameter :: sik_10 = selected_int_kind(10)',
                 'integer(kind=fwi_integer_t), '
                         'parameter :: srk_10_20 = '
                         'selected_real_kind(10, lit_int)',
                 'real(kind=fwr_srk_10_20_t), '
                         'intent(inout) :: real_arg',
                 'integer(kind=fwi_sik_10_t), '
                         'dimension(lit_int) :: int_arg'])

    def test_unneeded_param(self):
        unp = pyf.Parameter("unneeded", dtype=pyf.default_integer, expr="srk_10_20 + lit_int")
        sub_am = pyf.ArgManager(args=self.args, params=self.params+[unp])
        eq_(sub_am.arg_declarations(),
                ['integer(kind=fwi_integer_t), '
                        'parameter :: lit_int = 30-10',
                 'integer(kind=fwi_integer_t), '
                         'parameter :: sik_10 = selected_int_kind(10)',
                 'integer(kind=fwi_integer_t), '
                         'parameter :: srk_10_20 = '
                         'selected_real_kind(10, lit_int)',
                 'real(kind=fwr_srk_10_20_t), '
                         'intent(inout) :: real_arg',
                 'integer(kind=fwi_sik_10_t), '
                         'dimension(lit_int) :: int_arg'])
