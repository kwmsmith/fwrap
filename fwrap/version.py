# Set isrelease = True for release version.
isrelease = False
version = "0.1.0"

def set_rev():
    if isrelease: return
    global version
    from subprocess import Popen, PIPE
    try:
        stdout = Popen("hg identify --id".split(), stdout=PIPE).stdout
        global_id = stdout.read().strip()
    except OSError:
        global_id = "unknown"
    version = "%sdev_%s" % (version, global_id)

set_rev()
