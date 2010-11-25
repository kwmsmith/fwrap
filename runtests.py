#!/usr/bin/python

import os, sys, re, shutil, unittest, doctest

WITH_CYTHON = True

TEST_DIRS = ['compile', 'errors', 'run', 'pyregr']
TEST_RUN_DIRS = ['run', 'pyregr']

flags_re = re.compile(r'^(!|C)\s+configure-flags:(.*)$', re.MULTILINE)

def parse_testcase_flag_sets(filename):
    with file(filename) as f:
        contents = f.read()
    result = []
    for m in flags_re.finditer(contents):
        result.append(m.group(2).split())
    if len(result) == 0:
        result = [[]]
    return result

class FwrapTestBuilder(object):
    def __init__(self, rootdir, workdir, selectors, exclude_selectors,
                 cleanup_workdir, cleanup_sharedlibs, verbosity=0,
                 configure_flags=()):
        self.rootdir = rootdir
        self.workdir = workdir
        self.selectors = selectors
        self.exclude_selectors = exclude_selectors
        self.cleanup_workdir = cleanup_workdir
        self.cleanup_sharedlibs = cleanup_sharedlibs
        self.verbosity = verbosity
        self.configure_flags = configure_flags

    def build_suite(self):
        suite = unittest.TestSuite()
        test_dirs = TEST_DIRS
        filenames = os.listdir(self.rootdir)
        filenames.sort()
        for filename in filenames:
            path = os.path.join(self.rootdir, filename)
            if os.path.isdir(path) and filename in test_dirs:
                suite.addTest(
                        self.handle_directory(path, filename))
        return suite

    def handle_directory(self, path, context):
        workdir = os.path.join(self.workdir, context)
        if not os.path.exists(workdir):
            os.makedirs(workdir)

        suite = unittest.TestSuite()
        filenames = os.listdir(path)
        filenames.sort()
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() not in (".f", ".f77", ".f90", ".f95"):
                continue
            if filename.startswith('.'): continue # certain emacs backup files
            basename = os.path.splitext(filename)[0]
            fqbasename = "%s.%s" % (context, basename)
            if not [1 for match in self.selectors if match(fqbasename)]:
                continue
            if self.exclude_selectors:
                if [1 for match in self.exclude_selectors if match(fqbasename)]:
                    continue
            if context in TEST_RUN_DIRS:
                test_class = FwrapRunTestCase
            else:
                test_class = FwrapCompileTestCase
            flag_sets = parse_testcase_flag_sets(os.path.join(path, filename))
            for extra_flags in flag_sets:
                suite.addTest(self.build_test(test_class, path, workdir, filename, extra_flags))
        return suite

    def build_test(self, test_class, path, workdir, filename, extra_flags):
        return test_class(path, workdir, filename,
                cleanup_workdir=self.cleanup_workdir,
                cleanup_sharedlibs=self.cleanup_sharedlibs,
                verbosity=self.verbosity,
                configure_flags=self.configure_flags + extra_flags)

class _devnull(object):

    def flush(self): pass
    def write(self, s): pass

    def read(self): return ''


class FwrapCompileTestCase(unittest.TestCase):
    def __init__(self, directory, workdir, filename,
            cleanup_workdir=True, cleanup_sharedlibs=True,
            verbosity=0, configure_flags=()):
        self.directory = directory
        self.workdir = workdir
        self.filename = filename
        self.cleanup_workdir = cleanup_workdir
        self.cleanup_sharedlibs = cleanup_sharedlibs
        self.verbosity = verbosity
        self.configure_flags = configure_flags
        unittest.TestCase.__init__(self)

    def shortDescription(self):
        return "wrapping %s" % self.filename

    def setUp(self):
        if self.workdir not in sys.path:
            sys.path.insert(0, self.workdir)

    def tearDown(self):
        try:
            sys.path.remove(self.workdir)
        except ValueError:
            pass
        if os.path.exists(self.workdir):
            if self.cleanup_workdir:
                for rmfile in os.listdir(self.workdir):
                    try:
                        rmfile = os.path.join(self.workdir, rmfile)
                        if os.path.isdir(rmfile):
                            shutil.rmtree(rmfile, ignore_errors=True)
                        else:
                            os.remove(rmfile)
                    except IOError:
                        pass
        else:
            os.makedirs(self.workdirs)

    def runTest(self):
        # fwrapc.py configure build fsrc...
        self.projname = os.path.splitext(self.filename)[0] + '_fwrap'
        self.projdir = os.path.join(self.workdir, self.projname)
        fq_fname = os.path.join(os.path.abspath(self.directory), self.filename)
        source_files = [fq_fname]
        pyf_file = '%s.pyf' % os.path.splitext(fq_fname)[0]
        conf_flags = self.configure_flags
        if os.path.exists(pyf_file):
            conf_flags.append('--pyf=%s' % pyf_file)
        argv = ['configure'] + conf_flags + ['build',
                '--name=%s' % self.projname,
                '--outdir=%s' % self.projdir]
        argv += source_files
        argv += ['install']
        fwrapc(argv=argv)

    def compile(self, directory, filename, workdir, incdir):
        self.run_wrapper(directory, filename, workdir, incdir)

    def run_wrapper(self, directory, filename, workdir, incdir):
        wrap(filename, directory, workdir)


class FwrapRunTestCase(FwrapCompileTestCase):
    def shortDescription(self):
        return "compiling and running %s" % self.filename

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        try:
            self.setUp()
            self.runTest()
            if self.projdir not in sys.path:
                sys.path.insert(0, self.projdir)
            doctest_mod_base = self.projname+'_doctest'
            doctest_mod_fqpath = os.path.join(self.directory, doctest_mod_base+'.py')
            shutil.copy(doctest_mod_fqpath, self.projdir)
            doctest.DocTestSuite(self.projname+'_doctest').run(result) #??
        except Exception:
            result.addError(self, sys.exc_info())
            result.stopTest(self)
        try:
            self.tearDown()
        except Exception:
            pass


class FileListExcluder:

    def __init__(self, list_file):
        self.excludes = {}
        for line in open(list_file).readlines():
            line = line.strip()
            if line and line[0] != '#':
                self.excludes[line.split()[0]] = True

    def __call__(self, testname):
        return testname.split('.')[-1] in self.excludes

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--no-cleanup", dest="cleanup_workdir",
                      action="store_false", default=True,
                      help="do not delete the generated C files (allows passing --no-cython on next run)")
    parser.add_option("--no-cleanup-sharedlibs", dest="cleanup_sharedlibs",
                      action="store_false", default=True,
                      help="do not delete the generated shared libary files (allows manual module experimentation)")
    parser.add_option("-x", "--exclude", dest="exclude",
                      action="append", metavar="PATTERN",
                      help="exclude tests matching the PATTERN")
    parser.add_option("-v", "--verbose", dest="verbosity",
                      action="count",
                      default=0,
                      help="display test progress, more v's for more output")
    parser.add_option("-T", "--ticket", dest="tickets",
                      action="append",
                      help="a bug ticket number to run the respective test in 'tests/bugs'")
    parser.add_option("-C", metavar="CONFIGUREFLAG", action="append",
                      dest="configure_flags", default=[],
                      help="passes flag on to the waf configure command "
                      "(example: -Cf77binding)")

    options, cmd_args = parser.parse_args()


    # RUN ALL TESTS!
    ROOTDIR = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'tests')
    WORKDIR = os.path.join(os.getcwd(), 'BUILD')
    if os.path.exists(WORKDIR):
        for path in os.listdir(WORKDIR):
            if path in ("support",): continue
            shutil.rmtree(os.path.join(WORKDIR, path), ignore_errors=True)
    if not os.path.exists(WORKDIR):
        os.makedirs(WORKDIR)

    from fwrap.fwrapc import fwrapc

    sys.stderr.write("Python %s\n" % sys.version)
    sys.stderr.write("\n")

    # insert cython.py/Cython source directory into sys.path
    cython_dir = os.path.abspath(os.path.join(os.path.pardir, os.path.pardir))
    sys.path.insert(0, cython_dir)

    test_bugs = False
    if options.tickets:
        for ticket_number in options.tickets:
            test_bugs = True
            cmd_args.append('.*T%s$' % ticket_number)
    if not test_bugs:
        for selector in cmd_args:
            if selector.startswith('bugs'):
                test_bugs = True

    selectors = [ re.compile(r, re.I|re.U).search for r in cmd_args ]
    if not selectors:
        selectors = [ lambda x:True ]

    # Check which external modules are not present and exclude tests
    # which depends on them (by prefix)

    exclude_selectors = []

    if options.exclude:
        exclude_selectors += [ re.compile(r, re.I|re.U).search for r in options.exclude ]

    if not test_bugs:
        exclude_selectors += [ FileListExcluder("tests/bugs.txt") ]

    test_suite = unittest.TestSuite()

    configure_flags = ['--%s' % x for x in options.configure_flags]

    filetests = FwrapTestBuilder(ROOTDIR, WORKDIR, selectors, exclude_selectors,
                                 options.cleanup_workdir, options.cleanup_sharedlibs,
                                 options.verbosity,
                                 configure_flags=configure_flags)
    test_suite.addTest(filetests.build_suite())

    unittest.TextTestRunner(verbosity=options.verbosity).run(test_suite)
