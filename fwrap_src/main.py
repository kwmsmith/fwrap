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

# Available options, key is the option and value is the section in the 
# config file where it should be found
options = {'config':None,
           'name':'general',
           'build':'general',
           'recompile':'general',
           'out_dir':'general',
           'f90':'compiler',
           'fflags':'compiler',
           'ldflags':'compiler'}
        

def wrap(source,**kargs):
    r"""Wrap the source given and compile if requested
    
    This function is the main driving routine for fwrap and for most use
    cases should be sufficient.  It performs argument validation, compilation
    of the base source if requested, parses the source, writes out the
    necessary fortran, c, and cython files for wrapping, and again compiles
    those into a module if requested.
    
    :Input:
     - *source* - (id) List of paths to source files, this must be in the
       order compilation must proceed in, i.e. if you have modules in your
       source, list the source files that contain the modules first.  Can also
       be a file containing a list of sources.
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
     - *ldflags* - (string) Linker flags used, used in linking final
       library.
     - *recompile* - (bool) Recompile all object files before creating shared
       library, default is True
    """
    # Read in config file if present and parse input options
    config_files = [os.path.join(os.path.dirname(__file__),'default.config')]
    if kargs.has_key('config'):
        config_files.append(config)
    configparser = ConfigParser.SafeConfigParser()
    files_parsed = configparser.read(config_files)
    if kargs.has_key('config'):
        if config not in files_parse:
            logger.warning("Could not open configuration file %s" % config)
    # We remove the config option here since we have already treated it
    options.pop('config')
    for opt in options.iterkeys():
        if kargs.has_key(opt):
            exec("%s = kargs[opt]" % opt)
        else:
            exec("%s = configparser.get(options[opt],opt)" % opt)
            
    # Do some option parsing
    out_dir = out_dir.strip()
    name.strip()
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    project_path = os.path.join(out_dir,name)
    if os.path.exists(project_path):
        raise ValueError("Project directory %s already exists" \
                % os.path.join(out_dir,name.strip()))
    else:
        name.strip()
        os.mkdir(project_path)
    # *** TODO: Check if distutils can use this fcompiler and f90
    logger.debug("Running with following options:")
    for opt in options:
        logger.debug("  %s = %s" % (opt,locals()[opt]))
    
    # Check to see if each source exists and expand to full paths
    raw_source = False
    source_files = []
    if isinstance(source,basestring):
        if os.path.exists(source):
            source_files = [source]
        else:
            # Put raw source in a temporary directory
            raw_source = True
            fh,source_path = tempfile.mkstemp(suffix='f90',text=True)
            fh.write(source)
            fh.close()
            source_files.append(source_path)
    # elif not isinstance(source,list):
    #     raise ValueError("Must provide a list of source files")
    if len(source_files) < 1:
        raise ValueError("Must provide at least one source to wrap.")
    for (i,source) in enumerate(source_files):
        if os.path.exists(source.strip()):
            source_files[i] = source.strip()
        else:
            raise ValueError("The source file %s does not exist." % source)
    logger.debug("Wrapping the following source:")
    for src in source_files:
        logger.debug("  %s" % src)
        
    import pdb; pdb.set_trace()
    
    # Build source if need be, this is set to False by default as this section
    # has not been done yet
    if build:
        logger.info("Compiling fortran source...")
        raise NotImplementedError("Building of object code not supported.")
        logger.info("Compiling was successful.")

    # Parse fortran using fparser
    logger.info("Parsing source files.")
    f_ast = parse(source_files)
    logger.info("Parsing was successful.")

    # Generate wrapper files
    logger.info("Wrapping fortran...")
    generate(f_ast,name,project_path)
    logger.info("Wrapping was successful.")
    
    # Generate library module if requested
    if build:
        logger.info("Compiling library module...")
        raise NotImplementError("Building of library module not supported.")
        logger.info("Compiling was successful.")
        
    # If raw source was passed in, we need to delete the temp file we created
    if raw_source:
        os.remove(source_files[0])
        

def parse(source_files,parser='fparser'):
    r"""Parse fortran code using parser specified
    
    :Input:
     - *source_files* - (list) List of valid source files
     - *parser* - (string) String representing one of the following supported
       fortran parsers (default = 'fparser'):
        - 'fparser' - Use fparser
    """
    if parser == 'fparser':
        import fwrap_parse
        ast = fwrap_parse.generate_ast(source_files)
    else:
        raise NotImplementedError("Parser %s not supported." % parser)
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
    generators = ( (generate_type_specs,(fort_ast,name)),
                   (generate_fc_f,(c_ast,name)),
                   (generate_fc_h,(c_ast,name)),
                   (generate_fc_pxd,(c_ast,name)),
                   (generate_cy_pxd,(cython_ast,name)),
                   (generate_cy_pyx,(cython_ast,name)) )
    for (generator,args) in generators:
        file_name, buf = generator(*args)
        try:
            fh = open(os.path.join(project_path,file_name),'w')
            fh.write(buf.getvalue())
            fh.close()
        except IOError:
            raise
        
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


if __name__ == "__main__":
    # Parse command line options
    parser = OptionParser("usage: fwrap [options] SOURCE_FILES",
                            version=__version__)
    
    parser.add_option('-m',dest='name',help='')
    parser.add_option('-C','--config',dest='config',help='')
    parser.add_option('-c','-b','--build',dest='build',action='store_true',help='')
    parser.add_option('-o','--out_dir',dest='out_dir',help='')
    parser.add_option('--f90',dest='f90',help='')
    parser.add_option('-F','--fcompiler',dest='fcompiler',help='')
    parser.add_option('-f','--fflags',dest='fflags',help='')
    parser.add_option('-l','--ldflags',dest='ldflags',help='')
    parser.add_option('-r','--recompile',action="store_true",dest='recompile',help='')
    parser.add_option('--no-recompile',action="store_false",dest='recompile',help='')
    
    parsed_options, source_files = parser.parse_args()
    
    # Loop over options and put in a dictionary for passing into wrap
    kargs = {}
    logger.debug("Command line arguments: ")
    for opt in options.iterkeys():
        if getattr(parsed_options,opt) is not None:
            kargs[opt] = getattr(parsed_options,opt)
            logger.debug("  %s = %s" % (opt,kargs[opt]))
    
    # Call main routine
    wrap(source_files,**kargs)
    sys.exit(0)
