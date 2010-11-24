#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

PROC_SUFFIX_TMPL = "%s_c"

KTP_MOD_NAME = "fwrap_ktp_mod"
KTP_MOD_SRC = "%s.f90" % KTP_MOD_NAME
KTP_HEADER_SRC = "fwrap_ktp_header.h"
KTP_PXD_HEADER_SRC = "fwrap_ktp.pxd"

FC_HDR_TMPL = "%s_fc.h"
FC_PXD_TMPL = "%s_fc.pxd"
FC_F_TMPL = "%s_fc.f90"
FC_F_TMPL_F77 = "%s_fc.f"

CY_PXD_TMPL = "%s.pxd"
CY_PYX_TMPL = "%s.pyx"
CY_PYX_IN_TMPL = "%s.pyx.in"

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

def get_fortran_constants_utility_code(f77=False):
    lines = []
    if not f77:
        for err_name in sorted(ERR_CODES):
            lines.append('integer, parameter :: %s = %d' %
                         (err_name, ERR_CODES[err_name]))
    else:
        for err_name in sorted(ERR_CODES):
            lines.append('integer %s' % err_name)
            lines.append('parameter (%s = %d)' %
                         (err_name, ERR_CODES[err_name]))
    return lines

