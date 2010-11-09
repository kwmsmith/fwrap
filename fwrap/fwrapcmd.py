#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith, Dag Sverre Seljebotn
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# encoding: utf-8

import os, sys
import argparse
import logging
import textwrap

PROJECT_FILE = 'fwrap.json'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def init_cmd(ctx):
    return 0

def add_cmd(ctx):
    return 0

def update_cmd(ctx):
    return 0

def status_cmd(ctx):
    if ctx.project_root is None:
        return no_project_response(ctx)

    return 0


def no_project_response(ctx):
    print textwrap.fill('Please run "fwrap init"; can not find project '
                        'file %s in this directory or any parent directory.' %
                        PROJECT_FILE)
    return 1

def create_argument_parser():
    parser = argparse.ArgumentParser(prog='fwrap',
                                     description='fwrap command line tool')
    subparsers = parser.add_subparsers(title='commands')

    #
    # init command
    #
    init = subparsers.add_parser('init')
    init.set_defaults(func=init_cmd)
    mode_group = init.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--temporary', action='store_true',
                            help=('generated wrappers are temporary build artifacts,'
                                  'and can not be manually modified'))
    mode_group.add_argument('--versioned', action='store_true',
                            help=('allow modification of generated wrappers, and employ '
                                  'VCS to manage changes (only git supported currently)'))

    init.add_argument('--no-buildsys', action='store_true',
                      help='do not set up a build system for the project')

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

    return parser
    
def fwrap_main(args):
    argparser = create_argument_parser()
    ctx = argparser.parse_args(args)
    ctx.cwd = os.getcwd()
    cwdlist = ctx.cwd.split(os.sep)
    while cwdlist:
        path = os.sep.join(cwdlist)
        if os.path.exists(os.path.join(path, PROJECT_FILE)):
            ctx.project_root = path
            break
        cwdlist.pop()
    else:
        ctx.project_root = None
    return ctx.func(ctx)
