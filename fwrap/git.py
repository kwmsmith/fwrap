#------------------------------------------------------------------------------
# Copyright (c) 2010 Kurt Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# Simple wrapper around command-line git
from subprocess import Popen, PIPE

def execproc(cmd):
    assert isinstance(cmd, (list, tuple))
    pp = Popen(cmd, stdout=PIPE, stderr=PIPE)
    retcode = pp.wait()
    if retcode != 0:
        raise RuntimeError('Return code %d: %s' % (retcode, ' '.join(cmd)))
    result = pp.stdout.read().strip()
    err = pp.stderr.read()
    return result

def execproc_with_default(cmd, default):
    try:
        return execproc(cmd)
    except OSError:
        return default


def cwd_rev():
    return execproc_with_default(['git', 'rev-parse', 'HEAD'], None)
    

def status(files=()):
    result = execproc(['git', 'status', '--porcelain'] + list(files))
    lines = result.split('\n')
    result = {}
    for line in lines:
        if line.strip() == '':
            continue
        index, work, fname = line[0], line[1], line[3:]
        result[fname] = (index, work)
    return result

def is_tracked(filename):
    return len(status([filename]).keys()) == 0

def clean_index_and_workdir():
    for fname, (index, work) in status().iteritems():
        if index not in ('?', ' ') or work not in ('?', ' '):
            return False
    return True

def add(files):
    assert not isinstance(files, str)
    execproc(['git', 'add'] + list(files))

def commit(message):
    execproc(['git', 'commit', '-m', message])
