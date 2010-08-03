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

PROC_SUFFIX_TMPL = "%s_c"

KTP_MOD_NAME = "fwrap_ktp_mod"
KTP_MOD_SRC = "%s.f90" % KTP_MOD_NAME
KTP_HEADER_SRC = "fwrap_ktp_header.h"
KTP_PXD_HEADER_SRC = "fwrap_ktp.pxd"

FC_HDR_TMPL = "%s_fc.h"
FC_PXD_TMPL = "%s_fc.pxd"
FC_F_TMPL = "%s_fc.f90"

CY_PXD_TMPL = "%s.pxd"
CY_PYX_TMPL = "%s.pyx"

GENCONFIG_SRC = "genconfig.f90"
TYPE_SPECS_SRC = "fwrap_type_specs.in"
MAP_SRC = "fwrap_type_map.out"

RETURN_ARG_NAME = "fw_ret_arg"
ERR_NAME = "fw_iserr__"
ERRSTR_NAME = "fw_errstr__"
ERRSTR_LEN = "fw_errstr_len"
FORT_MAX_ARG_NAME_LEN = 63

ERR_CODES = {
        ERRSTR_LEN : FORT_MAX_ARG_NAME_LEN,
        'FW_NO_ERR__' : 0,
        'FW_INIT_ERR__' : -1,
        'FW_CHAR_SIZE__' : 1,
        'FW_ARR_DIM__' : 2,
        }

