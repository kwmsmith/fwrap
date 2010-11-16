#------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
#------------------------------------------------------------------------------

# encoding: utf-8

import os
from optparse import OptionParser

from fwrap import constants
from fwrap import gen_config as gc
from fwrap import fc_wrap
from fwrap import cy_wrap
from fwrap.code import CodeBuffer, CodeBufferFixedForm, reflow_fort
from fwrap.configuration import Configuration

PROJNAME = 'fwproj'

def wrap(sources, name, options):
    r"""Generate wrappers for sources.

    The core wrapping routine for fwrap.  Generates wrappers for the sources
    list.  Compilation of the wrappers is left to external utilities, whether
    distutils or waf.

    :Input:
     - *sources* - (id) Path to source or a list of paths to source to be
       wrapped.
     - *name* - (string) Name of the project and the name of the resulting
       python module
    """

    # validate name
    name = name.strip()
    name = name.replace(' ', '_')

    # Check to see if each source exists and expand to full paths
    source_files = []
    def check(s):
        return os.path.exists(s)
    if isinstance(sources, basestring):
        if check(sources):
            source_files = [sources]
    elif isinstance(sources, (list, tuple)):
        for src in sources:
            if check(src):
                source_files.append(src)
    if not source_files:
        raise ValueError("Invalid source list. %r" % (sources))

    # Parse fortran using fparser, get fortran ast.
    f_ast = parse(source_files)

    # Generate wrapper files
    generate(f_ast, name, options)

def parse(source_files):
    r"""Parse fortran code returning parse tree

    :Input:
     - *source_files* - (list) List of valid source files
    """
    from fwrap import fwrap_parse
    ast = fwrap_parse.generate_ast(source_files)

    return ast

def generate(fort_ast, name, options):
    r"""Given a fortran abstract syntax tree ast, generate wrapper files

    :Input:
     - *fort_ast* - (`fparser.ProgramBlock`) Abstract syntax tree from parser
     - *name* - (string) Name of the library module

     Raises `Exception.IOError` if writing the generated code fails.
    """

    # Generate wrapping abstract syntax trees
    # logger.info("Generating abstract syntax tress for c and cython.")
    c_ast = fc_wrap.wrap_pyf_iface(fort_ast)
    cython_ast = cy_wrap.wrap_fc(c_ast)

    cfg = Configuration(f77binding=options.f77binding,
                        fc_wrapper_orig_types=options.f77binding)

    # Generate files and write them out
    generators = ( (generate_type_specs,(c_ast,name)),
                   (generate_fc_f,(c_ast,name,cfg)),
                   (generate_fc_h,(c_ast,name,cfg)),
                   (generate_fc_pxd,(c_ast,name)),
                   (generate_cy_pxd,(cython_ast,name)),
                   (generate_cy_pyx,(cython_ast,name,cfg)) )

    for (generator,args) in generators:
        file_name, buf = generator(*args)
        write_to_dir(os.getcwd(), file_name, buf)

def write_to_dir(dir, file_name, buf):
    fh = open(os.path.join(dir, file_name), 'w')
    try:
        if isinstance(buf, basestring):
            fh.write(buf)
        else:
            fh.write(buf.getvalue())
    finally:
        fh.close()

def generate_type_specs(f_ast, name):
    buf = CodeBuffer()
    gc.generate_type_specs(f_ast, buf)
    return constants.TYPE_SPECS_SRC, buf

def generate_cy_pxd(cy_ast, name):
    buf = CodeBuffer()
    fc_pxd_name = (constants.FC_PXD_TMPL % name).split('.')[0]
    cy_wrap.generate_cy_pxd(cy_ast, fc_pxd_name, buf)
    return constants.CY_PXD_TMPL % name, buf

def generate_cy_pyx(cy_ast, name, cfg):
    buf = CodeBuffer()
    cy_wrap.generate_cy_pyx(cy_ast, name, buf, cfg)
    return constants.CY_PYX_TMPL % name, buf

def generate_fc_pxd(fc_ast, name):
    buf = CodeBuffer()
    fc_header_name = constants.FC_HDR_TMPL % name
    fc_wrap.generate_fc_pxd(fc_ast, fc_header_name, buf)
    return constants.FC_PXD_TMPL % name, buf

def generate_fc_f(fc_ast, name, cfg):
    if not cfg.f77binding:
        buf = CodeBuffer()
        outfile = constants.FC_F_TMPL % name
    else:
        buf = CodeBufferFixedForm()
        outfile = constants.FC_F_TMPL_F77 % name
        
    for proc in fc_ast:
        proc.generate_wrapper(buf, cfg)
        
    if not cfg.f77binding:
        ret_buf = CodeBuffer()
        ret_buf.putlines(reflow_fort(buf.getvalue()))
    else:
        ret_buf = buf
        
    return outfile, ret_buf

def generate_fc_h(fc_ast, name, cfg):
    buf = CodeBuffer()
    fc_wrap.generate_fc_h(fc_ast, constants.KTP_HEADER_SRC, buf, cfg)
    return constants.FC_HDR_TMPL % name, buf

def fwrapper(use_cmdline, sources=None, **options):
    """
    Main entry point, called by cmdline script.
    """

    if sources is None:
        sources = []
    defaults = dict(name=PROJNAME)
    if options:
        defaults.update(options)
    usage ='''\
Usage: %prog --name=NAME fortran-source [fortran-source ...]
'''
    description = '''\
%prog is a commandline utility that automatically wraps Fortran code in C,
Cython, & Python.
'''
    parser = OptionParser(usage=usage, description=description)
    parser.set_defaults(**defaults)
    if use_cmdline:
        parser.add_option('-n', '--name', dest='name',
                          help='name for the project directory and extension module '
                          '[default: %default]')
        parser.add_option('--f77binding', action='store_true',
                          help='avoid iso_c_binding and use older f2py-style '
                          'wrapping instead')
        args = None
    else:
        args = sources
    parsed_options, source_files = parser.parse_args(args=args)
    if not source_files:
        parser.error("no source files")
    wrap(source_files, parsed_options.name, parsed_options)
    return 0
