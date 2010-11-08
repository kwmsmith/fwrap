#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# encoding: utf-8

import os, sys, shutil
import subprocess
from optparse import OptionParser, OptionGroup

PROJECT_OUTDIR = 'fwproj'
PROJECT_NAME = PROJECT_OUTDIR

def setup_dirs(dirname):
    p = os.path
    fwrap_path = p.abspath(p.dirname(__file__))
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

def proj_dir(name):
    return os.path.abspath(name)

def configure_cb(opts, args, orig_args):
    wipe_out(proj_dir(opts.outdir))
    setup_dirs(proj_dir(opts.outdir))

def build_cb(opts, args, argv):
    srcs = []
    for arg in args:
        larg = arg.lower()
        if larg.endswith('.f') or larg.endswith('.f90') or larg.endswith('.pyf'):
            srcs.append(os.path.abspath(arg))
            argv.remove(arg)

    dst = os.path.join(proj_dir(opts.outdir), 'src')
    for src in srcs:
        shutil.copy(src, dst)

def call_waf(opts, args, orig_args):
    if 'configure' in args:
        configure_cb(opts, args, orig_args)

    if 'build' in args:
        build_cb(opts, args, orig_args)

    py_exe = sys.executable

    waf_path = os.path.join(proj_dir(opts.outdir), 'waf')

    cmd = [py_exe, waf_path] + orig_args
    odir = os.path.abspath(os.curdir)
    os.chdir(proj_dir(opts.outdir))
    try:
        subprocess.check_call(cmd)
    finally:
        os.chdir(odir)

    return 0

def print_version():
    from fwrap.version import get_version
    vandl = """\
fwrap v%s
Copyright (C) 2010 Kurt W. Smith
Fwrap is distributed under an open-source license.   See the source for
licensing information.  There is NO warranty, not even for MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.
""" % get_version()
    print vandl

def fwrapc(argv):
    """
    Main entry point -- called by cmdline script.
    """

    subcommands = ('configure', 'gen', 'build')

    parser = OptionParser()
    parser.add_option('--version', dest="version",
                      action="store_true", default=False,
                      help="get version and license info and exit")

    # configure options
    configure_opts = OptionGroup(parser, "Configure Options")
    configure_opts.add_option("--name",
            help='name for the extension module [default %default]')
    configure_opts.add_option("--outdir",
            help='directory for the intermediate files [default %default]')
    parser.add_option_group(configure_opts)

    conf_defaults = dict(name=PROJECT_NAME, outdir=PROJECT_OUTDIR)
    parser.set_defaults(**conf_defaults)

    opts, args = parser.parse_args(args=argv)

    if opts.version:
        print_version()
        return 0

    if not ('configure' in args or 'build' in args):
        parser.print_usage()
        return 1

    return call_waf(opts, args, argv)
