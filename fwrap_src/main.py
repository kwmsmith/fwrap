import os
from optparse import OptionParser
from cStringIO import StringIO
from code import CodeBuffer

import constants
import pyf_iface as pyf
import gen_config as gc
import fc_wrap
import cy_wrap

def wrap(options):
    # Parsing goes here...
    f_ast = generate_ast()

    fc_ast = wrap_fc(f_ast)
    cy_ast = wrap_cy(fc_ast)

    gens = [(generate_genconfig, f_ast),
            (generate_fc_f, fc_ast),
            (generate_fc_h, fc_ast),
            (generate_fc_pxd, fc_ast),
            (generate_cy_pxd, cy_ast),
            (generate_cy_pyx, cy_ast)
            ]

    for gen, ast in gens:
        fname, buf = gen(ast, options)
        full_path = os.path.join(options.outdir, fname)
        fh = open(full_path, 'w')
        fh.write(buf.getvalue())
        fh.close()

def setup_project(projectname, outdir):
    fq_projdir = os.path.join(outdir, projectname)
    if os.path.isdir(fq_projdir):
        raise RuntimeError("Error, project directory %s already exists." % fq_projdir)
    os.mkdir(fq_projdir)
    return fq_projdir

def parse_and_validate_args():
    default_projname = 'fwproj'
    parser = OptionParser()
    parser.add_option('--outdir',
                      dest='outdir',
                      default=None,
                      help='output directory for fwrap sources, defaults to "%s"' % default_projname)
    parser.add_option('--indir',
                      dest='indir',
                      default=os.path.curdir,
                      help='directory of fortran source files')
    parser.add_option('--projname',
                      dest='projectname',
                      default=default_projname,
                      help='name of fwrap project.')

    options, args = parser.parse_args()

    if args:
        parser.error("error: leftover arguments '%s'" % args)

    # Validate projectname
    options.projectname = options.projectname.strip()

    # Validate indir and outdir
    if options.outdir is None:
        options.outdir = os.path.join(os.path.curdir, options.projectname)

    options.outdir = os.path.abspath(options.outdir)
    options.indir = os.path.abspath(options.indir)

    if not os.path.exists(options.indir):
        parser.error("error: indir must be a valid directory, given '%s'." % options.indir)

    if os.path.exists(options.outdir) and os.listdir(options.outdir):
        parser.error("error: outdir '%s' exists and is not empty.")
     
    if not os.path.exists(options.outdir):
        os.makedirs(options.outdir)

    return options

def generate_genconfig(f_ast, options):
    buf = CodeBuffer()
    gc.generate_genconfig(f_ast, buf)
    return constants.GENCONFIG_NAME, buf

def generate_cy_pyx(cy_ast, options):
    buf = CodeBuffer()
    cy_wrap.generate_cy_pyx(cy_ast, buf)
    return constants.CY_PYX_TMPL % options.projectname, buf

def generate_cy_pxd(cy_ast, options):
    buf = CodeBuffer()
    fc_pxd_name = (constants.FC_PXD_TMPL % options.projectname).split('.')[0]
    cy_wrap.generate_cy_pxd(cy_ast, fc_pxd_name, buf)
    return constants.CY_PXD_TMPL % options.projectname, buf
 
def generate_fc_pxd(fc_ast, options):
    buf = CodeBuffer()
    fc_header_name = constants.FC_HDR_TMPL % options.projectname
    fc_wrap.generate_fc_pxd(fc_ast, fc_header_name, buf)
    return constants.FC_PXD_TMPL % options.projectname, buf

def generate_fc_h(fc_ast, options):
    buf = CodeBuffer()
    fc_wrap.generate_fc_h(fc_ast, constants.KTP_HEADER_NAME, buf)
    return constants.FC_HDR_TMPL % options.projectname, buf

def wrap_cy(ast):
    return cy_wrap.wrap_fc(ast)
 
def wrap_fc(ast):
    return fc_wrap.wrap_pyf_iface(ast)

def generate_fc_f(fc_ast, options):
    buf = CodeBuffer()
    for proc in fc_ast:
        proc.generate_wrapper(buf)
    return constants.FC_F_TMPL % options.projectname, buf

def generate_ast(fsrc):
    # this is a stub for now...
    empty_func = pyf.Function(name='empty_func',
                    args=(),
                    return_type=pyf.default_integer)
    return [empty_func]
