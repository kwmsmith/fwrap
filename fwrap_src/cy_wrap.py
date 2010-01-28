

def generate_pyx(program_unit_list, buf):
    buf.write('''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func():
    return DP_c.empty_func_c()
'''
)

def generate_pxd(program_unit_list, buf):
    buf.write('''
cimport DP_c

cpdef api DP_c.fwrap_default_int empty_func()
'''
)
