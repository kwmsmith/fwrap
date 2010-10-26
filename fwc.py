#!/usr/bin/env python

"""
fwc.py -- new implementation of fwrapc command, replaces distutils nastiness
with comfort, speed & elegance of waf.
"""

import os, sys, shutil
from optparse import OptionParser, OptionGroup
from collections import defaultdict

import subprocess

PROJECT_OUTDIR = 'fwproj'

def setup_dirs(dirname):
    p = os.path
    fwrap_path = p.abspath(p.join(p.dirname(__file__), 'fwrap'))
    # set up the project directory.
    try:
        os.mkdir(dirname)
    except OSError:
        pass
    src_dir = os.path.join(dirname, 'src')
    try:
        os.mkdir(src_dir)
    except OSError:
        pass

    # cp waf and wscript into the project dir.
    fw_wscript = os.path.join(
            fwrap_path,
            'fwrap_wscript')

    shutil.copy(
            fw_wscript,
            os.path.join(dirname, 'wscript'))

    waf_path = os.path.join(
            fwrap_path,
            'waf')

    shutil.copy(
            waf_path,
            dirname)

def wipe_out(dirname):
    # wipe out everything and start over.
    shutil.rmtree(dirname, ignore_errors=True)

def proj_dir():
    return os.path.join(os.path.abspath(os.curdir), PROJECT_OUTDIR)

def configure_cb(opts, args, orig_args):
    wipe_out(proj_dir())
    setup_dirs(proj_dir())

def build_cb(opts, args, argv):
    srcs = []
    for arg in args:
        larg = arg.lower()
        if larg.endswith('.f') or larg.endswith('.f90'):
            srcs.append(os.path.abspath(arg))
            argv.remove(arg)

    dst = os.path.join(proj_dir(), 'src')
    for src in srcs:
        shutil.copy(src, dst)

def call_waf(opts, args, orig_args):
    if 'configure' in args:
        configure_cb(opts, args, orig_args)

    if 'build' in args:
        build_cb(opts, args, orig_args)

    py_exe = sys.executable

    waf_path = os.path.join(proj_dir(), 'waf')

    cmd = [py_exe, waf_path] + orig_args
    odir = os.path.abspath(os.curdir)
    os.chdir(proj_dir())
    try:
        subprocess.check_call(cmd)
    finally:
        os.chdir(odir)

    return 0

def main():
    subcommands = ('configure', 'gen', 'build')

    argv = sys.argv[1:]

    parser = OptionParser()
    parser.add_option('--version', dest="version",
                      action="store_true", default=False,
                      help="get version and license info and exit")

    parser.add_option('-v', dest='verbose', action='count', default=0)

    # configure options
    configure_opts = OptionGroup(parser, "Configure Options")
    configure_opts.add_option("--name",
            help='name for the extension module')
    parser.add_option_group(configure_opts)

    conf_defaults = dict(name="fwproj")
    parser.set_defaults(**conf_defaults)

    opts, args = parser.parse_args()

    if opts.version:
        from fwrap.main import print_version
        print_version()
        return 0

    if not ('configure' in args or 'build' in args):
        parser.print_usage()
        return 1

    return call_waf(opts, args, argv)

if __name__ == '__main__':
    import sys
    sys.exit(main())
