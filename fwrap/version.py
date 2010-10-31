#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

import os
from os import path

# Set isrelease = True for release version.
isrelease = False
base_version = "0.2.0"

def get_version():

    if isrelease: return base_version

    from subprocess import Popen, PIPE
    git_dir = path.join(path.dirname(path.dirname(__file__)), '.git')
    cmd = "git --git-dir=%s rev-parse --short HEAD" % git_dir
    try:
        pp = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        pp.wait()
        global_id = pp.stdout.read().strip()
        err_txt = pp.stderr.read()
    except OSError:
        global_id = "unknown"
    return "%sdev_%s" % (base_version, global_id)
