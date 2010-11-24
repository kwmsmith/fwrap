#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# encoding: utf-8

import os, sys
import argparse
import logging
import textwrap
from glob import glob
import tempfile
import shutil
import re
from warnings import warn
from textwrap import dedent
from fwrap import fwrapper
from fwrap import configuration
from fwrap import git
from fwrap.configuration import Configuration

BRANCH_PREFIX = '_fwrap'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

record_update_re = re.compile(r'.*head record update.*', re.IGNORECASE)

def check_in_directory_of(mainfile):
    path, base = os.path.split(mainfile)
    if os.path.realpath(path) != os.getcwd():
        raise NotImplementedError('Please change to the directory of %s' % mainfile)

def get_head_record_update_commit(rev):
    # Try to base on the following head record update commit,
    # otherwise use the commit itself
    children = git.children_of_commit(rev)
    if len(children) == 1:
        # TODO: Speed up by only querying up to parents of
        # wanted commit (i.e. git show --raw --format=format:%P rev,
        # then git rev-list --children HEAD ^parent1 ^parent2
        child_rev = children[0]
        if record_update_re.match(git.get_commit_title(child_rev)):
            return child_rev
        
    warn('Using rev %s directly, not child' % rev)
    return rev
    

def commit_wrapper(cfg, message, skip_head_commit=False):
    pyx_basename = cfg.get_pyx_basename()
    auxiliary_basenames = cfg.get_auxiliary_files()
    recorded_rev = cfg.git_head()
    message = 'FWRAP %s' % message
    git.add([pyx_basename] + auxiliary_basenames)
    git.commit(message)
    # That's it for content. However, we need to update the head
    # pointer to point to the commit just made. Simply search/replace
    # the file to make the change and commit again
    if not skip_head_commit:
        new_rev = git.cwd_rev()
        configuration.replace_in_file('head %s' % recorded_rev,
                                      'head %s' % new_rev,
                                      pyx_basename,
                                      expected_count=1)
        git.add([pyx_basename])
        git.commit('FWRAP Head record update in %s' % pyx_basename)
    head = git.cwd_rev()
    return head        

def create_cmd(opts):
    if os.path.exists(opts.wrapper_pyx) and not opts.force:
        raise ValueError('File exists: %s' % opts.wrapper_pyx)
    check_in_directory_of(opts.wrapper_pyx)
    cfg = Configuration(opts.wrapper_pyx, cmdline_options=opts)
    cfg.update_version()
    cfg.set_versioned_mode(opts.versioned)
    # Ensure that tree is clean, as we want to auto-commit
    if opts.versioned and not git.clean_index_and_workdir():
        raise RuntimeError('VCS state not clean, aborting')
    # Add wrapped files to configurtion
    for filename in opts.fortranfiles:
        cfg.add_wrapped_file(filename)
    # Create wrapper files
    created_files, routine_names = fwrapper.wrap(opts.fortranfiles, cfg.wrapper_name,
                                                 cfg)
    # Commit
    if opts.versioned:
        message = opts.message
        if message is None:
            message = 'Created wrapper %s' % os.path.basename(opts.wrapper_pyx)
        message = ('%s\n\nFiles wrapped:\n%s' %
                   (message, '\n'.join(opts.fortranfiles)))
        
        commit_wrapper(cfg, message)
    return 0

def checkout_new_branch_from_last_fwrap(cfg):
    rev = cfg.git_head()
    rev = get_head_record_update_commit(rev)
    temp_branch = git.create_temporary_branch(rev, BRANCH_PREFIX)
    git.checkout(temp_branch)
    return temp_branch

def print_file_status(filename):
    file_cfg = Configuration.create_from_file(filename)
    if file_cfg.version in (None, ''):
        return # not an Fwrapped file
    
    def status_label(has_changed):
        return 
    status_report = file_cfg.wrapped_files_status()
    any_changed = any(needs_update for f, needs_update in status_report)
    print '%s (%s):' % (filename,
                        'needs update, please run "fwrap update %s"' % filename
                        if any_changed else 'up to date')
    for wrapped_file, needs_update in status_report:
        print '    %s%s' % (wrapped_file,
                            ' (changed)' if needs_update else '')
    return any_changed

def status_cmd(opts):
    print 'TODO: Not yet .pyx.in-aware'
    if len(opts.paths) == 0:
        if opts.recursive:
            opts.paths = ['.']
        else:
            opts.paths = glob('*.pyx')
    for path in opts.paths:
        if not os.path.exists(path):
            raise ValueError('No such file or directory: %s' % path)
        if not opts.recursive and not os.path.isfile(path):
            raise ValueError('Please specify --recursive to query a directory')
    needs_update = False
    if opts.recursive:
        for path in opts.paths:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    if filename.endswith('.pyx'):
                        needs_update = needs_update or print_file_status(filename)
    else:
        for filename in opts.paths:
            if os.path.isfile(filename) and filename.endswith('.pyx'):
                needs_update = needs_update or print_file_status(filename)
    return 1 if needs_update else 0


def mergepyf_cmd(opts):
    check_in_directory_of(opts.wrapper_pyx)
    for f in [opts.wrapper_pyx, opts.pyf]:
        if not os.path.exists(f):
            raise ValueError('No such file: %s' % f)
    orig_cfg = Configuration.create_from_file(opts.wrapper_pyx)
    orig_branch = git.current_branch()
    cfg = orig_cfg.copy()
    cfg.update_version()
    cfg.git_head() # fail if not in git mode
    
    # Find routine names present in Fortran files that are not
    # present in pyf file, and set them as manually excluded.
    # Below we commit removal of this functions as a seperate commit,
    # to keep the history much cleaner.
    routines_in_fortran = fwrapper.find_routine_names(
        cfg.get_source_files(), cfg)
    routines_in_pyf = fwrapper.find_routine_names(
        [opts.pyf], cfg) # TODO: Reuse parse tree from this step below
    excluded_by_pyf = set(routines_in_fortran) - set(routines_in_pyf)
    cfg.exclude_routines(excluded_by_pyf)
    
    # Generate wrapper from .pyf to temporary location before
    # switching away from the branch.
    tmp_dir = tempfile.mkdtemp(prefix='fwrap-')
    try:
        created_files, routines_in_pyf = fwrapper.wrap([opts.pyf],
                      cfg.wrapper_name,
                      cfg,
                      output_directory=tmp_dir)

        # Potentially create an update branch
        if len(excluded_by_pyf) > 0:
            temp_branch = update_wrapper(cfg,
                                         skip_head_commit=True,
                                         message='Removing routines not present in %s' % opts.pyf)
        else:
            temp_branch = checkout_new_branch_from_last_fwrap(cfg)
        
        # Copy in generated wrapper based on pyf file
        for f in glob(os.path.join(tmp_dir, '*')):
            shutil.copy(f, '.')
    finally:
        shutil.rmtree(tmp_dir)

    message = opts.message
    if message is None:
        message = 'Creating wrapper based on pyf file: %s' % opts.pyf
    commit_wrapper(cfg, message)
    print_help_after_update(orig_branch, temp_branch)

def update_wrapper(cfg, skip_head_commit, message):
    if not git.is_tracked(cfg.get_pyx_filename()):
        raise RuntimeError('Not tracked by VCS, aborting: %s' % cfg.get_pyx_basename())
    if not git.clean_index_and_workdir():
        raise RuntimeError('VCS state not clean, aborting')

    # First, generate wrappers (since Fortran files have changed
    # on *this* tree). But generate them into a temporary location.
    tmp_dir = tempfile.mkdtemp(prefix='fwrap-')
    try:
        fwrapper.wrap(cfg.get_source_files(),
                      cfg.wrapper_name,
                      cfg,
                      output_directory=tmp_dir)
        # Then, create and check out _fwrap branch used for merging, and
        # copy files in
        temp_branch = checkout_new_branch_from_last_fwrap(cfg)
        for f in glob(os.path.join(tmp_dir, '*')):
            shutil.copy(f, '.')
    finally:
        print 'tmp_dir', tmp_dir
        #shutil.rmtree(tmp_dir)
    # Commit
    if message is None:
        message = 'Updated wrapper %s' % cfg.get_pyx_basename()
    commit_wrapper(cfg, message, skip_head_commit=skip_head_commit)
    return temp_branch

def update_cmd(opts):
    cfg = Configuration.create_from_file(opts.wrapper_pyx)
    cfg.git_head() # fail if not in git mode
    check_in_directory_of(opts.wrapper_pyx)
    orig_branch = git.current_branch()
    temp_branch = update_wrapper(cfg, False, opts.message)
    print_help_after_update(orig_branch, temp_branch)

def print_help_after_update(orig_branch, temp_branch):
    # Print help text
    print dedent('''\
       Branch "{temp_branch}" created and wrapper updated. Please:

         a) Merge in any manual changes to the wrapper, e.g.,
         
                git merge {orig_branch}

            PS! Please do not rebase at this step. Otherwise you may
            make it impossible to do "fwrap update" in the future.
            
         b) Once everything is working, merge back and delete the
            temporary branch. 
            
                git checkout {orig_branch}
                git merge {temp_branch}
                git branch -d {temp_branch}
    '''.format(**locals()))
    
def no_project_response(opts):
    print textwrap.fill('Please run "fwrap init"; can not find project '
                        'file %s in this directory or any parent directory.' %
                        PROJECT_FILE)
    return 1

def create_argument_parser():
    parser = argparse.ArgumentParser(prog='fwrap',
                                     description='fwrap command line tool')
    subparsers = parser.add_subparsers(title='commands')

    #
    # create command
    #
    create = subparsers.add_parser('create')
    create.set_defaults(func=create_cmd)
    create.add_argument('-f', '--force', action='store_true',
                        help=('overwrite existing wrapper'))    
    create.add_argument('--versioned', action='store_true',
                        help=('allow modification of generated wrappers, and employ '
                              'VCS to manage changes (only git supported currently)'))    
    create.add_argument('-m', '--message',
                        help=('commit log message'))
    configuration.add_cmdline_options(create.add_argument)
    create.add_argument('wrapper_pyx')
    create.add_argument('fortranfiles', metavar='fortranfile', nargs='+')
    
    #
    # update command
    #
    update = subparsers.add_parser('update')
    update.set_defaults(func=update_cmd)
    update.add_argument('-m', '--message',
                        help=('commit log message'))
    update.add_argument('wrapper_pyx')

    #
    # mergepyf command
    #
    mergepyf = subparsers.add_parser('mergepyf')
    mergepyf.set_defaults(func=mergepyf_cmd)
    mergepyf.add_argument('wrapper_pyx')
    mergepyf.add_argument('-m', '--message',
                        help=('commit log message'))
    mergepyf.add_argument('pyf')

    #
    # status command
    #

    status = subparsers.add_parser('status')
    status.set_defaults(func=status_cmd)
    status.add_argument('-r', '--recursive', action='store_true',
                        help='Recurse subdirectories')
    status.add_argument('paths', metavar='path', nargs='*')

    return parser
    
def fwrap_main(args):
    argparser = create_argument_parser()
    opts = argparser.parse_args(args)
    if hasattr(opts, 'wrapper_pyx'):
        if (not opts.wrapper_pyx.endswith('.pyx') and
            not opts.wrapper_pyx.endswith('.pyx.in')):
            raise ValueError('Cython wrapper file name must end in .pyx or .pyx.in')

    return opts.func(opts)

