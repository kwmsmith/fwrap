#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# encoding: utf-8

import os, sys
import argparse
import logging
import textwrap
import glob
from fwrap import fwrapper
from fwrap import configuration

PROJECT_FILE = 'fwrap.json'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def create_cmd(opts):
    if os.path.exists(opts.wrapper_pyx) and not opts.force:
        raise ValueError('File exists: %s' % opts.wrapper_pyx)
    cfg = configuration.Configuration(cmdline_options=opts)
    cfg.update()
    for filename in opts.fortranfiles:
        cfg.add_wrapped_file(filename)
    fwrapper.wrap(opts.fortranfiles, opts.wrapper_name, cfg)
    return 0

def add_cmd(opts):
    raise NotImplementedError()

def update_cmd(opts):
    raise NotImplementedError()


def print_file_status(filename):
    file_cfg = configuration.Configuration.create_from_file(filename)
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
    if len(opts.paths) == 0:
        if opts.recursive:
            opts.paths = ['.']
        else:
            opts.paths = glob.glob('*.pyx')
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
    configuration.add_cmdline_options(create.add_argument)
    create.add_argument('wrapper_pyx')
    create.add_argument('fortranfiles', metavar='fortranfile', nargs='+')
    
    #
    # add command
    #
    add = subparsers.add_parser('add')
    add.set_defaults(func=add_cmd)


    #
    # update command
    #
    update = subparsers.add_parser('update')
    update.set_defaults(func=update_cmd)

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
        if not opts.wrapper_pyx.endswith('.pyx'):
            raise ValueError('Cython wrapper file name must end in .pyx')
        opts.wrapper_name = opts.wrapper_pyx[:-4]
    return opts.func(opts)
