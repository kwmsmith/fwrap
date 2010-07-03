#!/usr/bin/env python
# encoding: utf-8
r"""
Empty help!

:Author:
"""

import os
import sys
import logging
from optparse import OptionParser
from cStringIO import StringIO
from code import CodeBuffer, reflow_fort

import constants
import pyf_iface as pyf
import gen_config as gc
import fc_wrap
import cy_wrap

logger = logging.getLogger('fwrap')
        

def wrap(source_files=[], name="fwproj", build=False, build_dir='./fw_build',
            fort_compiler=None, fort_flags='', link_flags='', recompile=True,
            src_list=None):
    r"""
    :Input:
     - *source_files* - (id) List of paths to source files, this must be in the
       order compilation must proceed in, i.e. if you have modules in your
       source, list the source files that contain the modules first.  Can also
       be a file containing a list of sources.
     - *name* - (string) Name of the python module produced
     - *build* - (bool) Compile all source into a shared library for importing
       in python, default is True
     - *build_dir* - (string) Path where build products are placed
     - *fort_compiler* - (string) Fortran compiler requested, defaults to 
       distutils choice of compilers
     - *fort_flags* - (string) Compilation flags used, appended to the end of 
       distutils compilation run
     - *link_flags* - (string) Linker flags used, used in linking final
       library.
     - *recompile* - (bool) Recompile all object files before creating shared
       library, default is True
     - *src_list* - (string) Path to file containing a new line delimited list 
       of source files.  The source files will be appeneded to the list given
       in source_files or create it otherwise.
    """
    # Check to see if each source exists and expand to full paths
    if isinstance(source_files,basestring):
        if os.path.exists(source_files):
            source_files = [source_files]
        else:
            raise NotImplementedError("Direct source wrapping not supported.")
    elif not isinstance(source_files,list):
        raise ValueError("Must provide a list of source files")
    if src_list is not None:
        if isinstance(src_list,basestring):
            if os.path.exists(src_list):
                src_file = open(src_list,'r')
                for line in src_file:
                    source_files.append(line)
    if len(source_files) < 1:
        raise ValueError("Must provide a list of source files")
    for (i,source) in enumerate(source_files):
        if os.path.exists(os.path.abspath(source)):
            source_files[i] = os.path.abspath(source)
        else:
            raise ValueError("The source file %s does not exist." % source)

    # Validate some of the options
    for opt in ['name','build_dir','fort_flags','link_flags']:
        if not isinstance(locals()[opt],basestring):
            raise ValueError('Option "%s" must be a string' % opt)
    if not isinstance(build,bool):
        raise ValueError('Option "build" must be a bool.')
    if not os.path.exists(os.path.abspath(build_dir)):
        build_dir = os.path.abspath(build_dir)
    else:
        raise ValueError("Build directory %s already exists" \
                            % build_dir)
    name.strip()
    if fort_compiler is not None:
        if not isinstance(fort_compiler,basestring):
            raise ValueError('Option fort_compiler must be a string.')
    # TODO: Check if distutils can use this compiler
    
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
    generate(f_ast,name,build_dir)
    logger.info("Wrapping was successful.")
    
    # Generate library module if requested
    if build:
        logger.info("Compiling library module...")
        raise NotImplementError("Building of library module not supported.")
        logger.info("Compiling was successful.")
        

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

def generate(fort_ast,name,build_dir='./'):
    r"""Given a fortran abstract syntax tree ast, generate wrapper files
    
    :Input:
     - *fort_ast* - (`fparser.ProgramBlock`) Abstract syntax tree from parser
     - *name* - (string) Name of the library module
     - *build_dir* - (string) Path to build directory, defaults to './'
     
     Raises `IOError`
    """
    
    # Generate wrapping abstract syntax trees
    logger.info("Generating abstract syntax tress for c and cython.")
    c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
    cython_ast = cy_wrap.wrap_fc(fort_ast)
    
    # Generate files and write them out
    generators = ( (generate_genconfig,(fort_ast)),
                   (generate_type_specs,(fort_ast)),
                   (generate_fc_f,(c_ast,name)),
                   (generate_fc_h,(c_ast,name)),
                   (generate_fc_pxd,(cython_ast,name)),
                   (generate_cy_pxd,(cython_ast,name)),
                   (generate_cy_pyx,(cython_ast,name)) )
                   
    for (generator,args) in generators:
        file_name, buf = generator(*args)
        try:
            path = os.path.join(build_dir, file_name)
            fh = open(path,'w')
            fh.write(buff.getvalue())
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
    parser = OptionParser("usage: %prog [options] arg")
    
    parser.add_option('-m',dest='name',help='')
    parser.add_option('-c','--build',dest='build',action='store_true',help='')
    parser.add_option('-b','--build_dir',dest='build_dir',help='')
    parser.add_option('-F','--fort_compiler',dest='fort_compiler',help='')
    parser.add_option('-f','--fort_flags',dest='fort_flags',help='')
    parser.add_option('-L','--link_flags',dest='link_flags',help='')
    parser.add_option('-r','--recompile',action="store_true",dest='recompile',help='')
    parser.add_option('--no-recompile',action="store_false",dest='recompile',help='')
    parser.add_option('--src-list',dest='src_list',help='')
    
    parser.set_defaults(name="fwproj",build=False,build_dir="./fw_build",
                            fort_flags='',link_flags='',recompile=True,
                            src_list=None)
    
    options, source_files = parser.parse_args()

    try:
        wrap(source_files,name=options.name,build=options.build,
            build_dir=options.build_dir,fort_compiler=options.fort_compiler,
            fort_flags=options.fort_flags,link_flags=options.link_flags,
            recompile=options.recompile,src_list=options.src_list)
    except:
        logger.critical(''.join(('Traceback\n',
            ''.join( traceback.format_stack() ))))
        logger.critical("fwrap.wrap failed")
        sys.exit(1)
    sys.exit(0)
