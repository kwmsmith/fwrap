.. fwrap documentation master file, created by
   sphinx-quickstart on Tue May 18 21:00:46 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

+++++++++++++++++++++++++++++++++++++
Fortran for Speed, Python for Comfort
+++++++++++++++++++++++++++++++++++++

Fwrap wraps Fortran code in C, Cython and Python.  It focuses on Fortran 90 and
95, and will work with Fortran 77 so long as you limit yourself to "sane"
Fortran 77. [#sane-def]_ 

Fwrap is licensed under the new BSD license.

Fwrap is in beta-stage until otherwise indicated.  All commandline options and
public APIs are subject to change.

Fwrap changed its SCM from Mercurial to Git (github with a mirror on
sourceforge).  You can access the main development repository 
`here on github <http://github.com/kwmsmith/fwrap>`_.

Download Fwrap
==============

Get the lastest version `here <https://sourceforge.net/projects/fwrap/files/>`_.
    https://sourceforge.net/projects/fwrap/files/

Dependencies
============

`Python <http://python.org>`_
    Tested with 2.5 & 2.6 (2.4 in the near future, 3.x planned)

`NumPy <http://numpy.scipy.org/>`_ 
    Tested with NumPy >= 1.3.0

`Cython <http://www.cython.org/>`_ 
    Tested with Cython >= 0.11

**A Fortran 90 compiler**

    Known to work with:

      * ``gfortran`` >= 4.4.1

      * ``ifort`` >= 11.1

      * ``g95`` >= 0.92


Bug reports, Wiki & Mailing list
================================

`Fwrap trac <https://sourceforge.net/apps/trac/fwrap/>`_
    For bug reports, wiki pages, etc.

`<http://groups.google.com/group/fwrap-users>`_
    Questions, comments, patches, help...

Development
===========

`Git repository <http://github.com/kwmsmith/fwrap>`_
    To get the latest development version

`Development blog <http://fortrancython.wordpress.com/>`_
    For all fwrap-related news

Documentation
=============

"Official" documentation is nearly non-existent at the moment, and 
these documents mostly serve as a place to dump notes
while developing.

.. toctree::
   :maxdepth: 2

   doc/compatibility

Some helpful links
------------------

`Sourceforge support wiki <https://sourceforge.net/apps/trac/sourceforge/wiki/WikiStart>`_

`Fortran standards <http://gcc.gnu.org/wiki/GFortranStandards>`_

.. rubric:: Footnotes

.. [#sane-def]
   By "sane", we mean don't use `ENTRY`, `EQUIVALENCE`, STATEMENT functions, or
   other dark corners of Fortran 77.  If you don't know what these are, count
   yourself lucky.


..  Indices and tables
..  ==================

..  * :ref:`genindex`

..  * :ref:`modindex`
