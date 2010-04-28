from fwrap_ktp cimport *

cdef extern from "DP_fc.h":
    fwrap_default_int empty_func_c()
