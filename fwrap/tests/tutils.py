from nose.tools import eq_

def remove_common_indent(s):
    if not s:
        return s
    lines_ = s.splitlines()

    # remove spaces from ws lines
    lines = []
    for line in lines_:
        if line.rstrip():
            lines.append(line.rstrip())
        else:
            lines.append("")

    fst_line = None
    for line in lines:
        if line:
            fst_line = line
            break

    ws_count = 0
    for ch in fst_line:
        if ch == ' ':
            ws_count += 1
        else:
            break

    if not ws_count: return s

    ret = []
    for line in lines:
        line = line.rstrip()
        if line:
            assert line.startswith(' '*ws_count)
            ret.append(line[ws_count:])
        else:
            ret.append('')
    return '\n'.join(ret)

def compare(s1, s2):
    ss1 = remove_common_indent(s1.rstrip())
    ss2 = remove_common_indent(s2.rstrip())
    for idx, lines in enumerate(zip(ss1.splitlines(), ss2.splitlines())):
        L1, L2 = lines
        assert L1 == L2, "\n%s\n != \n%s%\nat line %d: '%s' != '%s'" % (ss1, ss2, idx, L1, L2)
