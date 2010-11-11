Compatibility modes
===================


Avoiding ``iso_c_binding``
--------------------------

Some Fortran compilers do not support the ``iso_c_binding`` module
used for Fortran/C interopability.  In particular, this applies to
Fortran 77 compilers, although it also applies to some older Fortran
90 compilers.

By passing the ``--no-iso-c-binding`` flag to the ``fwrapper``
command, one instead makes blatant assumptions about how Fortran/C
interopability should work. This is less standard, but works well in
practice in many situations, and was often used earlier for Fortran/C
interopability.

* The same assumptions are made about types as in the ``f2py`` tool.
* To control name mangling, one can pass the ``f2py`` -style
  definitions to the C compiler when compiling the C source generated
  by Cython
