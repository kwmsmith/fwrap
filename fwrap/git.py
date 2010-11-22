#------------------------------------------------------------------------------
# Copyright (c) 2010 Kurt Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# Simple wrapper around command-line git
from subprocess import Popen, PIPE

def execproc(cmd, get_err=False):
    assert isinstance(cmd, (list, tuple))
    pp = Popen(cmd, stdout=PIPE, stderr=PIPE)
    retcode = pp.wait()
    if retcode != 0:
        raise RuntimeError('Return code %d: %s' % (retcode, ' '.join(cmd)))
    result = pp.stdout.read().strip()
    err = pp.stderr.read()
    if get_err:
        return result, err
    else:
        return result

def execproc_canfail(cmd):
    assert isinstance(cmd, (list, tuple))
    pp = Popen(cmd, stdout=PIPE, stderr=PIPE)
    retcode = pp.wait()
    result = pp.stdout.read().strip()
    err = pp.stderr.read()
    return retcode, result, err

def execproc_with_default(cmd, default):
    try:
        return execproc(cmd)
    except OSError:
        return default


def cwd_rev():
    return execproc_with_default(['git', 'rev-parse', 'HEAD'], None)

def current_branch():
    return execproc(['git', 'rev-parse', '--symbolic-full-name',
                     '--abbrev-ref', 'HEAD'])

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

def create_temporary_branch(start_point, prefix):
    # TODO: Ensure/make this work on localized systems
    # Should probably use lower-level tool...
    for suffix in [''] + ['_%d' % i for i in range(2, 100)]:
        branch_name = prefix + suffix
        ret, out, err = execproc_canfail(['git', 'branch', branch_name, start_point])
        if ret == 0:
            return branch_name
        elif 'already exists' not in err:
            raise Exception('git error: %s' % err)
    raise Exception('Too many branches start with %s (delete some?)' % prefix)

def checkout(branch):
    execproc(['git', 'checkout', branch])

def children_of_commit(rev):
    lines = execproc(['git', 'rev-list', '--children', 'HEAD']).split('\n')
    for line in lines:
        items = line.split()
        # items = [parent, child, child, ...]
        if items[0] == rev:
            return items[1:]
    raise Exception('Commit not found: %s' % rev)

def get_commit_title(rev):
    lines = execproc(['git', 'show', '--raw', '--format=format:%s', rev]).split('\n')
    return lines[0]
