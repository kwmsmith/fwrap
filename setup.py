import os
from distutils.core import setup

scripts = []

if os.name == 'posix':
    scripts = ['bin/fwrapc']
else:
    scripts = ['fwrapc.py']

setup(name="fwrap",
      version="0.1a1",
      description="Tool to wrap Fortran 77/90/95 code in C, Cython & Python.",
      author="Kurt W. Smith",
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
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
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
