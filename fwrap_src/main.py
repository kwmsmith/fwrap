import os
from optparse import OptionParser
from cStringIO import StringIO

import constants
import pyf_iface as pyf
import gen_config as gc
import fc_wrap
import cy_wrap

def main():
    options, args = parse_and_validate_args()
    options.fq_projdir = setup_project(options.projectname, options.outdir)
    wrap(options, args)

def wrap(options, args):
    # Parsing goes here...
    ast = generate_ast()

    funcs_templ = [(fc_wrap.generate_fortran, "%s_c.f90"),
                   (fc_wrap.generate_h, "%s_c.h"),
                   (fc_wrap.generate_pxd, "%s_c.pxd"),
                   (cy_wrap.generate_pyx, "%s_cy.pyx"),
                   (cy_wrap.generate_pxd, "%s_cy.pxd")]

    for func, templ in funcs_templ:
        buf = StringIO()
        func(ast, buf)
        fname = templ % options.projectname
        full_path = os.path.join(options.fq_projdir, fname)
        fh = open(full_path, 'w')
        fh.write(buf.getvalue())
        buf.close()
        fh.close()

def setup_project(projectname, outdir):
    fq_projdir = os.path.join(outdir, projectname)
    if os.path.isdir(fq_projdir):
        raise RuntimeError("Error, project directory %s already exists." % fq_projdir)
    os.mkdir(fq_projdir)
    return fq_projdir

def parse_and_validate_args():
    parser = OptionParser()
    parser.add_option('--outdir',
                      dest='outdir',
                      default=os.path.curdir,
                      help='base of output directory')
    parser.add_option('--indir',
                      dest='indir',
                      default=os.path.curdir,
                      help='directory of fortran source files')
    parser.add_option('--projname',
                      dest='projectname',
                      default='untitled',
                      help='name of fwrap project -- will be the name of the directory.')
    options, args = parser.parse_args()

    # Validate indir and outdir
    options.outdir = os.path.abspath(options.outdir)
    options.indir = os.path.abspath(options.indir)
    if not os.path.exists(options.outdir):
        parser.error("--outdir option must be a valid directory, given '%s'." % options.outdir)
    if not os.path.exists(options.indir):
        parser.error("--indir option must be a valid directory, given '%s'." % options.indir)

    # Validate projectname
    options.projectname = options.projectname.strip()

    return options, args

def generate_genconfig(ast, buf):
    gc.generate_genconfig(ast, buf)

def generate_cy_pyx(ast, buf):
    cy_wrap.generate_cy_pyx(ast, buf)

def generate_cy_pxd(ast, projname, buf):
    fc_pxd_name = constants.FC_PXD_TMPL % projname
    cy_wrap.generate_cy_pxd(ast, fc_pxd_name, buf)
 
def generate_fc_pxd(ast, projname, buf):
    fc_header_name = constants.FC_HDR_TMPL % projname
    fc_wrap.generate_fc_pxd(ast, fc_header_name, buf)

def generate_fc_h(ast, buf):
    fc_wrap.generate_fc_h(ast, constants.KTP_HEADER_NAME, buf)

def wrap_cy(ast):
    return cy_wrap.wrap_fc(ast)
 
def wrap_fc(ast):
    return fc_wrap.wrap_pyf_iface(ast)

def generate_fc_f(ast, buf):
    for proc in ast:
        proc.generate_wrapper(buf)

def generate_ast(fsrc):
    # this is a stub for now...
    empty_func = pyf.Function(name='empty_func',
                    args=(),
                    return_type=pyf.default_integer)
    return [empty_func]
