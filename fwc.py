#!/usr/bin/env python

"""
fwc.py -- new implementation of fwrapc command, replaces distutils nastiness
with comfort, speed & elegance of waf.
"""

import os, sys, shutil
from optparse import OptionParser, OptionGroup
from collections import defaultdict

import subprocess

def subargs_split(sbcmds, argv):
    dd = {}
    if '' in sbcmds:
        raise ValueError('empty string not a valid subcommand')
    cur_subcmd = ''
    dd[cur_subcmd] = []
    for arg in argv:
        if arg in sbcmds:
            if arg in dd:
                raise ValueError("duplicate subcommand '%s'" % arg)
            cur_subcmd = arg
            dd[cur_subcmd] = []
        else:
            dd[cur_subcmd].append(arg)
    return dd

def configure_cb(opts, args, orig_args):
    p = os.path
    fwrap_path = p.abspath(p.join(p.dirname(__file__), 'fwrap'))
    # set up the project directory.
    proj_dir = os.path.join(os.path.abspath(os.curdir), opts.name)
    try:
        os.mkdir(proj_dir)
    except OSError:
        pass
    src_dir = os.path.join(proj_dir, 'src')
    try:
        os.mkdir(src_dir)
    except OSError:
        pass

    # cp the wscript into the project dir.
    fw_wscript = os.path.join(
            fwrap_path,
            'fwrap_wscript')

    shutil.copy(
            fw_wscript,
            os.path.join(proj_dir, 'wscript'))

    waf_path = os.path.join(
            fwrap_path,
            'waf')

    shutil.copy(
            waf_path,
            proj_dir)

    py_exe = sys.executable

    cmd = [py_exe, waf_path, 'configure'] + orig_args
    odir = os.path.abspath(os.curdir)
    os.chdir(proj_dir)
    try:
        subprocess.check_call(cmd)
    finally:
        os.chdir(odir)

if __name__ == '__main__':
    subcommands = ('configure', 'gen', 'build')

    argv = sys.argv[1:]

    subargs = subargs_split(subcommands, argv)

    # global options
    global_parser = OptionParser()
    global_opts = OptionGroup(global_parser, "Global Options")
    global_parser.remove_option('--help') # we handle help ourselves.
    global_opts.add_option('-h', '--help', action="store_true",
                      default=False,
                      help="show this help message and exit")
    global_opts.add_option('--version', dest="version",
                      action="store_true", default=False,
                      help="get version and license info and exit")
    global_parser.add_option_group(global_opts)

    # configure options
    configure_parser = OptionParser()
    configure_opts = OptionGroup(configure_parser, "Configure Options")
    configure_opts.add_option("--name",
            help='name for the project directory and extension module')
    configure_parser.add_option_group(configure_opts)

    conf_defaults = dict(name="fwproj")
    configure_parser.set_defaults(**conf_defaults)

    if '' in subargs:
        gopts, gargs = global_parser.parse_args(subargs[''])
        if gopts.help:
            global_parser.print_help()
            configure_parser.print_help()
        print "global opts, args:", gopts, gargs

    if 'configure' in subargs:
        orig_args = subargs['configure']
        copts, cargs = configure_parser.parse_args(orig_args)
        print "conf opts, args:", copts, cargs
        configure_cb(copts, cargs, orig_args)
