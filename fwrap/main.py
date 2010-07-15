#!/usr/bin/env python
# encoding: utf-8
r"""This module contains the interface for fwrap and the command line routine



:Authors:
"""

__version__ = "0.1.0"

import os
import sys
import logging
import traceback
import ConfigParser
import tempfile
from optparse import OptionParser
from cStringIO import StringIO
from code import CodeBuffer, reflow_fort

import constants
import pyf_iface as pyf
import gen_config as gc
import fc_wrap
import cy_wrap

# Logging utility, see log.config for default configuration
logger = logging.getLogger('fwrap')

# Available options parsed from default config files
_config_parser = ConfigParser.SafeConfigParser() 
fp = open(os.path.join(os.path.dirname(__file__), 'default.config'),'r')
_config_parser.readfp(fp)
fp.close()
_available_options = {}
for section in _config_parser.sections():
    for opt in _config_parser.options(section):
        _available_options[opt] = section
# Remove source option
_available_options.pop('source')
# Add config option
_available_options['config'] = None
        

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
     - *recompile* - (bool) Recompile all object files before creating shared
       library, default is True
     - *override* - (bool) If a project directory already exists in the
       out_dir specified, remove it and create a fresh project.
    """
    # Read in config file if present and parse input options
    if kargs.has_key('config'):
        file_list = _config_parser.read(kargs['config'])
        if kargs['config'] not in file_list:
            logger.warning("Could not open configuration file %s" % kargs['config'])
    for opt in _available_options.iterkeys():
        if not opt == 'config':
            if kargs.has_key(opt):
                exec("%s = kargs[opt]" % opt)
            else:
                exec("%s = _config_parser.get(_available_options[opt],opt)" % opt)
    
    # Do some option parsing
    out_dir = out_dir.strip()
    name.strip()
    logger.debug("Running with following options:")
    for opt in _available_options:
        if not (opt == 'source' or opt == 'config'):
            logger.debug("  %s = %s" % (opt,locals()[opt]))
    
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    project_path = os.path.join(out_dir,name)
    if os.path.exists(project_path):
        if override:
            logger.debug("Removing %s" % project_path)
            os.removedirs(project_path)
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
    config_source = _config_parser.get('general','source')
    if len(config_source) > 0:
        for src in config_source.split(','):
            source_files.append(src)
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
    if len(source_files) < 1:
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
    logger.info("Parsing was successful.")

    # Generate wrapper files
    logger.info("Wrapping fortran...")
    generate(f_ast,name,project_path)
    logger.info("Wrapping was successful.")

    # generate setup.py file
    file_name, buf = generate_setup(name, 'fwrap_setup.log',
                            source_files, libraries, library_dirs, extra_objects)
    write_to_project_dir(project_path, file_name, buf)
    
    # Generate library module if requested
    if build:
        logger.info("Compiling sources and generating extension module...")
        odir = os.path.abspath(os.curdir)
        try:
            os.chdir(project_path)
            logger.info("Changing to project directory %s" % project_path)
            fcomp_option = '--fcompiler=%s' % fcompiler
            from distutils.core import run_setup
            run_setup(file_name,
                    script_args=['config', fcomp_option,
                                 'build_ext', fcomp_option,
                                 '--inplace'])
        finally:
            if os.path.abspath(os.curdir) != odir:
                logger.info("Returning to %s" % odir)
                os.chdir(odir)
        logger.info("Compiling was successful.")
        
    # If raw source was passed in, we need to delete the temp file we created
    if raw_source:
        os.remove(source_files[0])
        

def parse(source_files):
    r"""Parse fortran code returning parse tree
    
    :Input:
     - *source_files* - (list) List of valid source files
    """
    import fwrap_parse
    return fwrap_parse.generate_ast(source_files)

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
    cy_wrap.generate_cy_pyx(cy_ast, buf)
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

def main():
    # Parse command line options
    parser = OptionParser("usage: fwrap [options] SOURCE_FILES",
                            version=__version__)
    
    parser.add_option('-m', dest='name', help='')
    parser.add_option('-C', '--config', dest='config', help='')
    parser.add_option('-c',  '-b',  '--build',  dest='build',
                        action='store_true', default=False,  help='')
    parser.add_option('-o', '--out_dir', dest='out_dir', help='')
    parser.add_option('-F', '--fcompiler', dest='fcompiler', help='')
    parser.add_option('-f', '--fflags',  dest='fflags',  action='callback',
                        callback=varargs_cb,  help='')
    parser.add_option('--objects', dest='extra_objects', action='callback',
                        callback=varargs_cb, help='')
    parser.add_option('-l', dest='libraries',  action='append')
    parser.add_option('-L', dest='library_dirs',  action='append')
    parser.add_option('-r', '--recompile', action="store_true",
                        dest='recompile', help='')
    parser.add_option('--no-recompile', action="store_false", dest='recompile', help='')
    parser.add_option('--override', action="store_true", dest='override', help='')
    parser.add_option('--no-override', action="store_false", dest='override', help='')
    
    parsed_options, source_files = parser.parse_args()
    
    # Loop over options and put in a dictionary for passing into wrap
    kargs = {}
    logger.debug("Command line arguments: ")
    for opt in _available_options.iterkeys():
        try:
            if getattr(parsed_options,opt) is not None:
                kargs[opt] = getattr(parsed_options,opt)
                logger.debug("  %s = %s" % (opt,kargs[opt]))
        except:
            pass
    
    # Call main routine
    wrap(source_files,**kargs)
    sys.exit(0)
