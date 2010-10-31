#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

from subprocess import call
import sys

call(("%s/bin/nosetests -s fwrap/tests" % sys.exec_prefix).split())
