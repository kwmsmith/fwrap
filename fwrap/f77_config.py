#------------------------------------------------------------------------------
# Copyright (c) 2010
#
# Dag Sverre Seljebotn <dagseljebotn@gmail.com>
# Pearu Peterson <pearu@ioc.ee> (code taken from f2py)
#
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

#
# Code to generate type specification files, in Fortran 77 binding mode:
#
#   - fwrap_ktp_header.h
#   - fwrap_ktp.pxd
#   - fwrap_ktp.pxi
#
# No compiler probing is currently going on, this file simply helps
# output some static assumptions. In particular, assume that
# -fdefault-integer-8 is NOT passed (in the case of gfortran).
# Mostly meant to be used with build systems that currently work
# with f2py (which make the same blatant assumptions).
#
# Also contains utility code for Fortran 77 binding mode (name
# mangling macros).

import fwrap.pyf_iface as pyf
import fwrap.gen_config as gc
from fwrap.fwrap_parse import create_dtype

def get_f77_ctps():
    # Essentially simulates the effect of parsing
    # all possible types (integer, integer*2, and so on)
    # and associate the type
    f77_type_table = [
        ('integer', [
            (None, 'c_int'),
            (1, 'c_char'),
            (2, 'c_short'),
            (4, 'c_int'),
            (8, 'c_long')]),
        ('real', [
            (None, 'c_float'),
            (4, 'c_float'),
            (8, 'c_double'),
            (12, 'c_long_double'),
            (16, 'c_long_double')]),
        ('doubleprecision', [
            (None, 'c_float')]),
        ('complex', [
            (None, 'c_float_complex'),
            (8, 'c_float_complex'),
            (16, 'c_double_complex'),
            (24, 'c_long_double_complex'),
            (32, 'c_long_double_complex')]),
        ('doublecomplex', [
            (None, 'c_double_complex')]),
        ('character', [
            (None, 'c_char')]),
        ('logical', [
            (None, 'c_int'),
            (1, 'c_char'),
            (2, 'c_short'),
            (4, 'c_int'),
            (8, 'c_long')]),
    ]

    ctps = []
    for name, subtypes in f77_type_table:
        for length, fc_type in subtypes:
            dtype = create_dtype(name, length=length, kind=None)
            ctp = gc.ctp_from_dtype(dtype)
            ctp.fc_type = fc_type
            ctps.append(ctp)

            # We assume that kind and length are the same for now.
            # This is WRONG, e.g., for the g77 compiler, but allows
            # us to use F90 testcases with gfortran in f77binding
            # mode during development. TODO: Consider disabling this
            # or implement build time detection.
            if length is not None:
                dtype = create_dtype(name, length=None, kind=length)
                ctp = gc.ctp_from_dtype(dtype)
                ctp.fc_type = fc_type
                ctps.append(ctp)
    return ctps

def strip_leading_whitespace(block):
    return '\n'.join(x.lstrip() for x in block.split('\n'))

name_mangling_utility_code = strip_leading_whitespace("""\
#if !defined(NO_FORTRAN_MANGLING)
    #if !defined(PREPEND_FORTRAN) && defined(NO_APPEND_FORTRAN) && !defined(UPPERCASE_FORTRAN)
        #define NO_FORTRAN_MANGLING 1
    #endif
#endif
#if defined(NO_FORTRAN_MANGLING)
    #define F_FUNC(f,F) f
#else
    #if defined(PREPEND_FORTRAN)
        #if defined(NO_APPEND_FORTRAN)
            #if defined(UPPERCASE_FORTRAN)
                #define F_FUNC(f,F) _##F
            #else
                #define F_FUNC(f,F) _##f
            #endif
        #else
            #if defined(UPPERCASE_FORTRAN)
                #define F_FUNC(f,F) _##F##_
            #else
                #define F_FUNC(f,F) _##f##_
            #endif
        #endif
    #else
        #if defined(NO_APPEND_FORTRAN)
            #if defined(UPPERCASE_FORTRAN)
                #define F_FUNC(f,F) F
            #else
                #error Can not happen
            #endif
        #else
            #if defined(UPPERCASE_FORTRAN)
                #define F_FUNC(f,F) F##_
            #else
                #define F_FUNC(f,F) f##_
            #endif
        #endif
    #endif
#endif
""")

def gen_type_map_files():
    ctps = get_f77_ctps()
    for func, fname, args in [(gc.write_header, 'ktp.h', ()),
                              (gc.write_pxd, 'ktp.pxd', ('FOO',)),
                              (gc.write_pxi, 'ktp.pxi', ())]:
        with file(fname, 'w') as buf:
            func(ctps, buf, *args)

if __name__ == '__main__':
    gen_type_map_files()#ctps, task.outputs, write_f90_mod=False)

    
