#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Fwrap project nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#------------------------------------------------------------------------------

# encoding: utf-8

import os
import sys
import shutil
import logging
import tempfile
from optparse import OptionParser
from fwrap.code import CodeBuffer, reflow_fort
from numpy.distutils.fcompiler import CompilerNotFound
from numpy.distutils.command import config_compiler
from fwrap.version import get_version

from fwrap import constants
from fwrap import gen_config as gc
from fwrap import fc_wrap
from fwrap import cy_wrap

import logging, logging.config


def _setup_config():
    pass
    # Available options parsed from default config files
    # _config_parser = ConfigParser.SafeConfigParser()
    # fp = open(os.path.join(os.path.dirname(__file__), 'default.config'),'r')
    # _config_parser.readfp(fp)
    # fp.close()
    # _available_options = {}
    # for section in _config_parser.sections():
        # for opt in _config_parser.options(section):
            # _available_options[opt] = section
    # Remove source option
    # _available_options.pop('source')
    # Add config option
    # _available_options['config'] = None


def get_projectpath(out_dir, name):
    return os.path.abspath(os.path.join(out_dir, name))


def shutdown_logging(projectpath):

    logging.shutdown()

    for fname in os.listdir(os.path.curdir):
        if fname.endswith('.log'):
            abspath = os.path.abspath(os.path.join(os.path.curdir, fname))
            shutil.move(abspath, projectpath)



def wrap(source=None,**kargs):
    r"""Wrap the source given and compile if requested

    This function is the main driving routine for fwrap and for most use
    cases should be sufficient.  It performs argument validation, compilation
    of the base source if requested, parses the source, writes out the
    necessary fortran, c, and cython files for wrapping, and again compiles
    those into a module if requested.

    :Input:
     - *source* - (id) Path to source or a list of paths to source to be
       wrapped.  It can also be a piece of raw source in a string (assumed if
       the single string does not lead to a valid file).  If you give a list
       of source files, make sure that they are in the order that they must
       be compiled due to dependencies like modules.  Note that if a source
       list exists in the configuration file as well, the source argument is
       appended to the end of the source list.  If you need to append to the
       front of the list, you need to modify the configuration file.
     - *config* - (string) Path to configuration file.  This will be config
       file is read in first so arguments to the command supercede the
       settings in the config file.
     - *name* - (string) Name of the project and the name of the resulting
       python module
     - *build* - (bool) Compile all source into a shared library for importing
       in python, default is True
     - *out_dir* - (string) Path where project build is placed
     - *f90* - (string) Compiler or path to compiler, default is 'gfortran'
     - *fcompiler* - (string) Class name of fortran compiler requested, this
       name is the one that distutils recognizes.  Default is 'gnu95'.
     - *fflags* - (string) Compilation flags used, appended to the end of
       distutils compilation run
     - *libraries* - (list)
     - *library_dirs* - (list)
     - *override* - (bool) If a project directory already exists in the
       out_dir specified, remove it and create a fresh project.
    """
    # # Read in config file if present and parse input options
    # if kargs.has_key('config'):
        # file_list = _config_parser.read(kargs['config'])
        # if kargs['config'] not in file_list:
            # logger.warning("Could not open configuration file %s" % kargs['config'])
    # for opt in _available_options.iterkeys():
        # if not opt == 'config':
            # if kargs.has_key(opt):
                # exec("%s = kargs[opt]" % opt)
            # else:
                # exec("%s = _config_parser.get(_available_options[opt],opt)" % opt)

    # Do some option parsing
    out_dir = kargs.get('out_dir')
    out_dir = out_dir.strip()
    name = kargs.get('name')
    name.strip()
    logger.debug("Running with following options:")
    # for opt in _available_options:
        # if not (opt == 'source' or opt == 'config'):
            # logger.debug("  %s = %s" % (opt,locals()[opt]))


    help_fcompiler = kargs.get('help_fcompiler')
    if help_fcompiler:
        from distutils.core import run_setup
        run_setup(file_name, script_args=make_scriptargs(kargs))
        return

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    project_path = get_projectpath(out_dir, name)

    if os.path.exists(project_path):
        override = kargs.get('override')
        if override:
            logger.debug("Removing %s" % project_path)
            shutil.rmtree(project_path)
            os.mkdir(project_path)
        else:
            raise ValueError("Project directory %s already exists" \
                % os.path.join(out_dir,name.strip()))
    else:
        name.strip()
        os.mkdir(project_path)
    # *** TODO: Check if distutils can use this fcompiler and f90

    # Check to see if each source exists and expand to full paths
    raw_source = False
    source_files = []
    # Parse config file source list
    # config_source = _config_parser.get('general','source')
    # if len(config_source) > 0:
        # for src in config_source.split(','):
            # source_files.append(src)
    # Parse function call source list
    if source is not None:
        if isinstance(source,basestring):
            if os.path.exists(source):
                source_files = [source]
            else:
                # Assume this is raw source, put in temporary directory
                raw_source = True
                fh,source_path = tempfile.mkstemp(suffix='f90',text=True)
                fh.write(source)
                fh.close()
                source_files.append(source_path)
        elif (isinstance(source,list) or isinstance(source,tuple)):
            for src in source:
                source_files.append(src)
        else:
            raise ValueError("Must provide either a string or list of source")

    # Validate and parse source list
    if not source_files:
        raise ValueError("Must provide at least one source to wrap.")
    for (i,src) in enumerate(source_files):
        # Expand variables and path
        source_files[i] = os.path.expanduser(os.path.expandvars(src.strip()))
        if not os.path.exists(source_files[i]):
            raise ValueError("The source file %s does not exist." % source_files[i])
    logger.debug("Wrapping the following source:")
    for src in source_files:
        logger.debug("  %s" % src)

    # Parse fortran using fparser
    logger.info("Parsing source files.")
    f_ast = parse(source_files)

    # XXX: total hack: turns out that when fparser sets up its logging with
    # logger.configFile(...), **the logging module disables all existing
    # loggers**, which includes fwrap's logger.  This completely breaks our
    # logging functionality; thankfully it's simple turn it back on again.
    logger.disabled = 0

    logger.info("Parsing was successful.")

    # Generate wrapper files
    logger.info("Wrapping fortran...")
    generate(f_ast, name, project_path)
    logger.info("Wrapping was successful.")

    # generate setup.py file
    libraries = kargs.get('libraries')
    library_dirs = kargs.get('library_dirs')
    extra_objects = kargs.get('extra_objects')
    log_name = 'fwrap_setup.log'
    if logging.DEBUG >= fwlogging.console_handler.level:
        log_name = ""
    file_name, buf = generate_setup(name, log_name, source_files,
                                libraries, library_dirs, extra_objects)
    write_to_project_dir(project_path, file_name, buf)

    # Generate library module if requested
    logger.info("Compiling sources and generating extension module...")
    odir = os.path.abspath(os.curdir)
    try:
        os.chdir(project_path)
        logger.info("Changing to project directory %s" % project_path)
        from distutils.core import run_setup
        run_setup(file_name, script_args=make_scriptargs(kargs))
    finally:
        if os.path.abspath(os.curdir) != odir:
            logger.info("Returning to %s" % odir)
            os.chdir(odir)
    logger.info("Compiling was successful.")

    # If raw source was passed in, we need to delete the temp file we created
    if raw_source:
        os.remove(source_files[0])

def check_fcompiler(fcompiler):
    return fcompiler in allowed_fcompilers()

def allowed_fcompilers():
    from numpy.distutils import fcompiler
    fcompiler.load_all_fcompiler_classes()
    return fcompiler.fcompiler_class.keys()


def parse(source_files):
    r"""Parse fortran code returning parse tree

    :Input:
     - *source_files* - (list) List of valid source files
    """
    from fwrap import fwrap_parse
    ast = fwrap_parse.generate_ast(source_files)

    return ast

def generate(fort_ast,name,project_path):
    r"""Given a fortran abstract syntax tree ast, generate wrapper files

    :Input:
     - *fort_ast* - (`fparser.ProgramBlock`) Abstract syntax tree from parser
     - *name* - (string) Name of the library module
     - *out_dir* - (string) Path to build directory, defaults to './'

     Raises `Exception.IOError` if writing the generated code fails.
    """

    # Generate wrapping abstract syntax trees
    logger.info("Generating abstract syntax tress for c and cython.")
    c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
    cython_ast = cy_wrap.wrap_fc(c_ast)

    # Generate files and write them out
    generators = ( (generate_type_specs,(c_ast,name)),
                   (generate_fc_f,(c_ast,name)),
                   (generate_fc_h,(c_ast,name)),
                   (generate_fc_pxd,(c_ast,name)),
                   (generate_cy_pxd,(cython_ast,name)),
                   (generate_cy_pyx,(cython_ast,name)) )
    for (generator,args) in generators:
        file_name, buf = generator(*args)
        write_to_project_dir(project_path, file_name, buf)

def write_to_project_dir(project_path, file_name, buf):
    fh = open(os.path.join(project_path,file_name),'w')
    try:
        if isinstance(buf, basestring):
            fh.write(buf)
        else:
            fh.write(buf.getvalue())
    finally:
        fh.close()

def generate_setup(name, log_file,
                   sources,
                   libraries=None,
                   library_dirs=None,
                   extra_objects=None):
    tmpl = '''\
from fwrap.fwrap_setup import setup, fwrap_cmdclass, configuration

cfg_args = %(CFG_ARGS)s

cfg = configuration(projname='%(PROJNAME)s', **cfg_args)
setup(log='%(LOG_FILE)s', cmdclass=fwrap_cmdclass, configuration=cfg)
'''
    sources = [os.path.abspath(source) for source in sources]
    extra_objects = [os.path.abspath(eo) for eo in extra_objects]
    cfg_args = {'extra_sources' : sources,
                'libraries' : libraries or [],
                'library_dirs' : library_dirs or [],
                'extra_objects' : extra_objects or [],
               }
    dd = {'PROJNAME': name,
            'LOG_FILE': log_file,
            'CFG_ARGS': repr(cfg_args)}

    return 'setup.py', (tmpl % dd)

def generate_genconfig(f_ast, name):
    buf = CodeBuffer()
    gc.generate_genconfig(f_ast, buf)
    return constants.GENCONFIG_SRC, buf

def generate_type_specs(f_ast, name):
    buf = CodeBuffer()
    gc.generate_type_specs(f_ast, buf)
    return constants.TYPE_SPECS_SRC, buf

def generate_cy_pxd(cy_ast, name):
    buf = CodeBuffer()
    fc_pxd_name = (constants.FC_PXD_TMPL % name).split('.')[0]
    cy_wrap.generate_cy_pxd(cy_ast, fc_pxd_name, buf)
    return constants.CY_PXD_TMPL % name, buf

def generate_cy_pyx(cy_ast, name):
    buf = CodeBuffer()
    cy_wrap.generate_cy_pyx(cy_ast, name, buf)
    return constants.CY_PYX_TMPL % name, buf

def generate_fc_pxd(fc_ast, name):
    buf = CodeBuffer()
    fc_header_name = constants.FC_HDR_TMPL % name
    fc_wrap.generate_fc_pxd(fc_ast, fc_header_name, buf)
    return constants.FC_PXD_TMPL % name, buf

def generate_fc_f(fc_ast, name):
    buf = CodeBuffer()
    for proc in fc_ast:
        proc.generate_wrapper(buf)
    ret_buf = CodeBuffer()
    ret_buf.putlines(reflow_fort(buf.getvalue()))
    return constants.FC_F_TMPL % name, ret_buf

def generate_fc_h(fc_ast, name):
    buf = CodeBuffer()
    fc_wrap.generate_fc_h(fc_ast, constants.KTP_HEADER_SRC, buf)
    return constants.FC_HDR_TMPL % name, buf

def varargs_cb(option, opt_str, value, parser):
    assert value is None
    value = []

    for arg in parser.rargs[:]:
        if arg.startswith('--') or arg.startswith('-'):
            break
        value.append(arg)
        del parser.rargs[0]

    setattr(parser.values, option.dest, value)

def make_scriptargs(kargs):

    for name in ('fcompiler', 'f90flags',
                 'f90exec', 'debug', 'noopt',
                 'noarch', 'opt', 'arch', 'build_ext',
                 ):
        exec("%s = kargs.get(name)" % name)

    check_fcompiler(fcompiler)

    fcopt = '--fcompiler=%s' % fcompiler
    scargs = []
    scargs += ['config', fcopt]
    scargs += ['config_fc']
    if debug:
        scargs += ['--debug']
    if noopt:
        scargs += ['--noopt']
    if noarch:
        scargs += ['--noarch']
    if opt:
        scargs += ['--opt=%s' % opt]
    if arch:
        scargs += ['--arch=%s' % arch]
    if f90exec:
        scargs += ['--f90exec=%s' % f90exec]
    if f90flags:
        scargs += ['--f90flags=%s' % f90flags]
        scargs += ['--f77flags=%s' % f90flags]

    scargs += ['build_src']

    if build_ext:
        scargs += ['build_ext', fcopt, '--inplace']

    return scargs

class fwlogging(object):

    ERROR, WARN, INFO, DEBUG = range(4)

    log_levels = {ERROR : 'ERROR',
                  WARN : 'WARN',
                  INFO : 'INFO',
                  DEBUG : 'DEBUG'}

    console_handler = None

    @staticmethod
    def set_console_level(verbose):
        verbose = min(verbose, fwlogging.DEBUG)
        verbose = max(verbose, fwlogging.ERROR)
        lvl = getattr(logging, fwlogging.log_levels[verbose])
        for handler in logger.handlers:
            if handler.stream == sys.stdout:
                if fwlogging.console_handler is None:
                    fwlogging.console_handler = handler
                handler.setLevel(lvl)

    @staticmethod
    def setup_logging():
        global logger
        # Default logging configuration file
        _DEFAULT_LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__),'log.config')

        # Setup loggers
        logging.config.fileConfig(_DEFAULT_LOG_CONFIG_PATH)

        # Logging utility, see log.config for default configuration
        logger = logging.getLogger('fwrap')

def print_version():
    vandl = """\
fwrap v%s
Copyright (C) 2010 Kurt W. Smith
Fwrap is distributed under an open-source license.   See the source for
licensing information.  There is NO warranty, not even for MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.
""" % get_version()
    print vandl


def main(use_cmdline, sources=None, logging=True, **options):

    fwlogging.setup_logging()

    if sources is None:
        sources = []

    defaults = dict(name='fwproj',
                    version=False,
                    build_ext=False,
                    out_dir=os.path.curdir,
                    f90flags='',
                    f90exec='',
                    extra_objects=[],
                    verbose=fwlogging.ERROR,
                    override=False,
                    help_fcompiler=False,
                    debug=False,
                    noopt=False,
                    noarch=False,
                    opt='',
                    arch='')

    if options:
        defaults.update(options)

    usage ='''\
Usage: %prog [options] fortran-source [fortran-source ...]
       %prog --build [compiler-specific options] fortran-source [fortran-source ...]
       %prog --help-fcompiler [compiler-specific options]
       %prog --help | --version
'''

    description = '''\
%prog is a commandline utility that automatically wraps Fortran code in C, Cython,
& Python, optionally building a Python extension module.
'''

    parser = OptionParser(usage=usage, description=description)
    parser.set_defaults(**defaults)

    if use_cmdline:

        parser.add_option('--help-fcompiler', action='store_true', dest='help_fcompiler',
                          help='output information about fortran compilers and exit')

        parser.add_option('-V', '--version', dest="version",
                          action="store_true",
                          help="get version and license info and exit")

        parser.add_option('-v', '--verbose', dest="verbose",
                          action='count',
                          help='the more v\'s (up to 3), the more chatty it gets')

        parser.add_option('-n', '--name', dest='name',
                          help='name for the project directory and extension module '
                          '[default: %default]')
        parser.add_option('-b',  '--build',  dest='build_ext', action='store_true',
                          help='create the extension module after generating wrappers [default: off]')
        parser.add_option('-o', '--out_dir', dest='out_dir',
                help='specify where the project directory is to be placed, '
                '[default: current directory]')

        parser.add_option('--override', action="store_true", dest='override',
                          help='clobber an existing project with the same name [default: off]')

        parser.add_option('--fcompiler', dest='fcompiler',
                          help='specify the fortran compiler to use, see \'--help-fcompiler\'')
        parser.add_option('--f90exec', dest='f90exec',
                          help=('Full path of the specified Fortran 90 compiler, '
                          'not necessary if numpy distutils can discover it (see --help-fcompiler)'))
        parser.add_option('--f90flags', dest='f90flags',
                          help='extra fortran compilation flags')
        parser.add_option('--objects', dest='extra_objects', action='callback',
                            callback=varargs_cb,
                            metavar='<object list>',
                          help='extra object files, archives, etc. to include in the extension module')
        parser.add_option('-L', dest='library_dirs',  action='append',
                          metavar='libdir',
                          help='add directory libdir to ld search path')
        parser.add_option('-l', dest='libraries',  action='append',
                          metavar='libname',
                          help='runtime library name to include during linking,'
                          ' e.g. -lgfortran or -lg95')

        parser.add_option('--debug', dest='debug', action='store_true',
                          help='include debug flags during compilation')
        parser.add_option('--noopt', dest='noopt', action='store_true',
                          help='remove all optimization flags during compilation')
        parser.add_option('--noarch', dest='noarch', action='store_true',
                          help='do not include architecture-specific flags during compilation')
        parser.add_option('--opt', dest='opt',
                          help='extra optimization flags to include during compilation')
        parser.add_option('--arch', dest='arch',
                          help='include target architecture during compilation')

        args = None

    else:
        args = sources

    parsed_options, source_files = parser.parse_args(args=args)

    if parsed_options.version:
        print_version()
        return 0

    fwlogging.set_console_level(parsed_options.verbose)

    out_dir, name = parsed_options.out_dir, parsed_options.name

    # Loop over options and put in a dictionary for passing into wrap
    logger.debug("Command line arguments: ")
    # for opt in _available_options.iterkeys():
        # try:
            # if getattr(parsed_options,opt) is not None:
                # kargs[opt] = getattr(parsed_options,opt)
                # logger.debug("  %s = %s" % (opt,kargs[opt]))
        # except:
            # pass

    retval = 0
    # Call main routine

    if parsed_options.help_fcompiler:
        config_compiler.show_fortran_compilers()
        return 0

    if not source_files:
        parser.error("no source files")

    try:
        wrap(source_files, **parsed_options.__dict__)
    except CompilerNotFound, m:
        print >>sys.stdout, m
        retval = 1
    finally:
        shutdown_logging(get_projectpath(out_dir, name))
    return retval
