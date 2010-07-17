from subprocess import call
import sys

call(("%s/bin/nosetests -s fwrap/tests" % sys.exec_prefix).split())
