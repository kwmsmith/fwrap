# Set isrelease = True for release version.
isrelease = False
base_version = "0.1.0"

def get_version():

    if isrelease: return base_version

    from subprocess import Popen, PIPE
    try:
        pp = Popen("hg identify --id --rev tip".split(), stdout=PIPE, stderr=PIPE)
        pp.wait()
        global_id = pp.stdout.read()
        err_txt = pp.stderr.read()
    except OSError:
        global_id = "unknown"
    return "%sdev_%s" % (base_version, global_id)
