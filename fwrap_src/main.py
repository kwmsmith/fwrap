import os
from optparse import OptionParser
from cStringIO import StringIO
from code import CodeBuffer

import constants
import pyf_iface as pyf
import gen_config as gc
import fc_wrap
import cy_wrap

def main():
    options, args = parse_args()
    wrap(args, options)

def wrap(source_files, options):

    validate_args(options, source_files)

    # Parsing goes here...
    f_ast = generate_ast(source_files)

    fc_ast = wrap_fc(f_ast)
    cy_ast = wrap_cy(fc_ast)

    # gens = [(generate_genconfig, f_ast),
    gens = [(generate_type_specs, f_ast),
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

def parse_args():
    default_projname = 'fwproj'
    parser = OptionParser()
    parser.add_option('--outdir',
                      dest='outdir',
                      default=None,
                      help='output directory for fwrap sources, defaults to "%s"' % default_projname)
    parser.add_option('--projname',
                      dest='projectname',
                      default=default_projname,
                      help='name of fwrap project.')

    options, args = parser.parse_args()

    return options, args

def validate_args(options, args):

    # Validate projectname
    options.projectname = options.projectname.strip()

    # Validate outdir
    if options.outdir is None:
        options.outdir = os.path.join(os.path.curdir, options.projectname)

    options.outdir = os.path.abspath(options.outdir)

    if os.path.exists(options.outdir) and os.listdir(options.outdir):
        parser.error("error: outdir '%s' exists and is not empty.")
     
    if not os.path.exists(options.outdir):
        os.makedirs(options.outdir)

    return options, args

def generate_type_specs(f_ast, options):
    buf = CodeBuffer()
    gc.generate_type_specs(f_ast, buf)
    return constants.TYPE_SPECS_SRC, buf

def generate_genconfig(f_ast, options):
    buf = CodeBuffer()
    gc.generate_genconfig(f_ast, buf)
    return constants.GENCONFIG_SRC, buf

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
    fc_wrap.generate_fc_h(fc_ast, constants.KTP_HEADER_SRC, buf)
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

def generate_ast(fsrcs):
    import fwrap_parse
    return fwrap_parse.generate_ast(fsrcs)
