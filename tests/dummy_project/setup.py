
import os,sys
# sys.path.insert(0, '/home/ksmith/Devel/fwrap/fwrap-dev-old')

from fwrap_setup import FwrapExtension, fwrap_build_ext, setup
sources = ['DP.f90', 'DP_fortran.f90']
ext = FwrapExtension(
            'DP_fwrap',
            sources= sources,
            fwrap_config_sources=[('genconfig.f90', 'config.f90')],
            fwrap_cython_sources=['DP_fwrap.pyx'],
            )
setup(cmdclass={'build_ext' : fwrap_build_ext},
        ext_modules = [ext])

