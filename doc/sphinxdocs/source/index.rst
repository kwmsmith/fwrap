.. fwrap documentation master file, created by
   sphinx-quickstart on Tue May 18 21:00:46 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Fortran for Speed, Python for Comfort
+++++++++++++++++++++++++++++++++++++

..  ..  .. toctree::
..  ..  :maxdepth: 2

Fwrap wraps Fortran code in C, Cython and Python.  It focuses on Fortran 90 and
95, and will work with Fortran 77 so long as you limit yourself to "sane"
Fortran 77. [#sane-def]_ 

Fwrap is licensed under the new BSD license.

.. note::
   Fwrap is under heavy development and is quickly approaching its first
   release.  This page is constantly being updated with new information and
   links.


Dependencies
============

`NumPy <http://numpy.scipy.org/>`_ 
    Tested with NumPy >= 1.3.0
`Cython <http://www.cython.org/>`_ 
    Tested with Cython >= 0.11
`Fparser <http://f2py.googlecode.com/svn/trunk/fparser/>`_ 
    Used by fwrap for parsing Fortran code (will be distributed with fwrap's
    releases)

And, of course a sufficiently recent version of `Python
<http://www.python.org/>`_ (tested with versions 2.5 and 2.6) and a Fortran 90
compiler.  `Gfortran <http://gcc.gnu.org/wiki/GFortran>`_ version >= 4.3.3
works well, as does Intel's `ifort
<http://software.intel.com/en-us/intel-compilers/>`_.

Bug reports, Wiki & Mailing list
================================

`Fwrap trac <https://sourceforge.net/apps/trac/fwrap/>`_
    For bug reports, wiki pages, etc.

`<http://groups.google.com/group/fwrap-users>`_
    Questions, comments, patches, help...

Development
===========

`Mercurial Repository <http://bitbucket.org/kwmsmith/fwrap-dev/>`_
    To get the latest development version

`Development blog <http://fortrancython.wordpress.com/>`_
    For all fwrap-related news

Some helpful links
------------------

`Sourceforge support wiki <https://sourceforge.net/apps/trac/sourceforge/wiki/WikiStart>`_

.. rubric:: Footnotes

.. [#sane-def]
   By "sane", we mean "don't use Fortran 77 features officially discouraged by
   the Fortran 9x standard."  This restriction will gradually relax as more F77
   features are supported.


..  Indices and tables
..  ==================

..  * :ref:`genindex`

..  * :ref:`modindex`
