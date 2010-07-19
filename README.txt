Fwrap: Wrap Fortran 77/90/95 in C, Cython & Python
==================================================

Fwrap is a utility that takes Fortran 77/90/95 source code and provides
cross-platform & cross-compiler wrappers in C, Cython & Python.

It wraps the basic functionality you'd expect (functions, subroutines, scalar
and array arguments for intrinsic types) and will eventually support all
features of Fortran 90/95 (derived types, C/Cython/Python callbacks, wrap
modules in Python classes).

It is currently under heavy construction.  The first public version, 0.1, is
coming soon.


Requirements
------------

Note: these requirements will loosen as more testing is done; if you would like
an earlier version of these requirements supported please email.

Fwrap requires & has been sucessfully tested on: 

 * Python >= 2.5, < 3.0

 * Cython >= 0.11.1

 * NumPy >= 1.3.0

 * A sufficiently modern Fortran 90 compiler.

Fwrap has been tested on three fortran compilers to date, but could benefit
from more testing on other compilers/other versions.  If you have another
version or a different compiler and use fwrap, please let the devs know.

Tested Fortran 90 compilers:

 * gfortran >= 4.4.1 (see note)

 * g95 >= 0.92

 * ifort >= 11.1

Note on gfortran:  gfortran version 4.3.3 (widely distributed with many OSes)
has a C binding bug that renders the compiler unusable for Fwrap's purposes.
Please let me know if you have success using version 4.3.[4-5], indicating that
this bug is fixed in the 4.3.x line.  (Gfortran works in 4.4.1 and later.)


Running the Tests
-----------------

Fwrap has a pretty good testsuite.  Getting it running will indicate if
everything is working on your system.  

For a failsafe setup, it is necessary to set environment flags to tell Fwrap
where to find your system's fortran runtime libraries.  For a bash shell, do
the following:

    $ export F90=/path/to/fortran/executable

    $ export LDFLAGS='-L/path/to/fortran/runtime/lib -l<runtimelibname>'

For gfortran:

    $ export F90=/usr/local/bin/gfortran

    $ export LDFLAGS='-L/usr/local/lib -lgfortran'

Then you can run the tests, again from this dir:

    $ python runtests.py -vv --fcompiler=gnu95 --no-cleanup

All the build products will be placed in a directory 'BUILD'.

If you have success or failure, we'd love to know.


More Information & Resources
----------------------------

Project homepage:

    http://fwrap.sourceforge.net/

Fwrap-users mailing list, for all questions & support:

    http://groups.google.com/group/fwrap-users

For fwrap news:

    http://fortrancython.wordpress.com/
