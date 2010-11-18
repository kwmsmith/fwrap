#------------------------------------------------------------------------------
# Copyright (c) 2010 Kurt Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# Simple wrapper around command-line git
from subprocess import Popen, PIPE

def execproc(cmd):
    # TODO: Spaces in filenames
    pp = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    pp.wait()
    result = pp.stdout.read().strip()
    err = pp.stderr.read()
    return result

def execproc_with_default(cmd, default):
    try:
        return execproc(cmd)
    except OSError:
        return default

def cwd_rev():
    return execproc_with_default("git rev-parse HEAD", None)
    
