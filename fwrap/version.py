#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

import os
from os import path
from fwrap.git import execproc_with_default

# Set isrelease = True for release version.
isrelease = False
base_version = "0.2.0"

def get_version():
    if isrelease: return base_version
    from subprocess import Popen, PIPE
    # TODO: Spaces in path
    git_dir = path.join(path.dirname(path.dirname(__file__)), '.git')
    cmd = "git --git-dir=%s rev-parse --short HEAD" % git_dir
    global_id = execproc_with_default(cmd.split(), "unknown")
    return "%sdev_%s" % (base_version, global_id)
