#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# encoding: utf-8

import os, sys
import argparse
import logging
import textwrap
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

def status_cmd(opts):
    
    return 0


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
    status.add_argument('wrapper_pyx')

    return parser
    
def fwrap_main(args):
    argparser = create_argument_parser()
    opts = argparser.parse_args(args)
    if opts.wrapper_pyx is not None:
        if not opts.wrapper_pyx.endswith('.pyx'):
            raise ValueError('Cython wrapper file name must end in .pyx')
        opts.wrapper_name = opts.wrapper_pyx[:-4]
    return opts.func(opts)
