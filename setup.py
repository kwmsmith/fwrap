#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

import os
from distutils.core import setup

scripts = []

scripts = ['fwrapc.py', 'fwrapper.py']

from fwrap.version import get_version

setup(name="fwrap",
      version=get_version(),
      description="Tool to wrap Fortran 77/90/95 code in C, Cython & Python.",
      author="Kurt W. Smith & contributors",
      author_email="kwmsmith@gmail.com",
      url="http://fwrap.sourceforge.net/",
      packages=[
          "fwrap",
          "fwrap.fparser"
        ],
      package_data = {
          "fwrap" : ["default.config", "log.config"],
          "fwrap.fparser" : ["log.config"],
        },
      scripts=scripts,
      classifiers = [
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: BSD License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Fortran",
          "Programming Language :: C",
          "Programming Language :: Cython",
          "Topic :: Software Development :: Code Generators",
          "Topic :: Software Development :: Libraries :: Python Modules"
        ],
     )
