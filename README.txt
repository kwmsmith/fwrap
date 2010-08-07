==================================================
Fwrap: Wrap Fortran 77/90/95 in C, Cython & Python
==================================================

Fwrap is a utility that takes Fortran 77/90/95 source code and
provides cross-platform & cross-compiler wrappers in C, Cython &
Python.

It wraps the basic functionality you'd expect (functions,
subroutines, scalar and array arguments for intrinsic types) and will
eventually support all features of Fortran 90/95 (derived types,
C/Cython/Python callbacks, wrap modules in Python classes).

It is currently under heavy construction and is to be considered beta
software until otherwise indicated.  All commandline options, APIs
etc. are subject to change.


Requirements
------------

Note: these requirements will loosen as more components are tested;
if you would like an earlier version of these requirements tested
please email the developers.

Fwrap has been sucessfully tested with:

 * Python 2.5 and 2.6 (2.4 likely coming soon, Py3 support is
   planned)

 * Cython >= 0.11.1

 * NumPy >= 1.3.0

 * A sufficiently modern Fortran 90 compiler.

Fwrap has been tested on three fortran compilers to date (see below),
but could benefit from more testing on other compilers/other
versions.  If you have another version or a different compiler and
use fwrap, please let the devs know.

Tested Fortran 90 compilers:

 * gfortran >= 4.4.1 (see note)

 * g95 >= 0.92

 * ifort >= 11.1

Note on gfortran:  The gfortran series 4.3.x >= 4.3.3 (widely
distributed with many OSes) has a C binding bug that renders the
compiler unusable for N-D arrays of type logical or character, where
N >= 3.  If you can avoid logical and character arrays more than 2
dimensions, then there's no problem. (Gfortran works in 4.4.1 and
later.)


Running the Tests
-----------------

Fwrap has a pretty good testsuite.  Getting it running will indicate
if everything is working on your system and is highly recommended
while Fwrap is in beta stage.

For a failsafe setup, it is necessary to set environment flags to
tell Fwrap where to find your system's fortran runtime libraries and
executable.  For a bash shell, do the following:

    $ export F90=/path/to/fortran/executable

    $ export LDFLAGS='-L/path/to/fortran/runtime/lib
     -l<runtimelibname>'

For gfortran:

    $ export F90=/usr/local/bin/gfortran

    $ export LDFLAGS='-L/usr/local/lib -lgfortran'

Then you can run the tests from the directory containing this
README.txt file:

    $ python runtests.py -vv --fcompiler=gnu95 --no-cleanup

All the build products will be placed in a directory 'BUILD' which
can be safely removed.

If you have success or failure, we'd love to know.


More Information & Resources
----------------------------

See USAGE.txt for basic commandline use.

See the examples directory for some samples to get started.

Project homepage:

    http://fwrap.sourceforge.net/

Fwrap-users mailing list, for all questions & support:

    http://groups.google.com/group/fwrap-users

For fwrap news:

    http://fortrancython.wordpress.com/

.. vim:tw=69
