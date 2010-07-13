from nose.tools import eq_

def remove_common_indent(s):
    ws_count = 0
    fst_line = s.splitlines()[0]
    for ch in fst_line:
        if ch == ' ':
            ws_count += 1
        else:
            break

    if not ws_count: return s

    ret = []
    for line in s.splitlines():
        line = line.rstrip()
        if line:
            assert line[:ws_count] == ' '*ws_count
            ret.append(line[ws_count:])
        else:
            ret.append('')
    return '\n'.join(ret)

def compare(s1, s2):
    ss1 = remove_common_indent(s1.rstrip())
    ss2 = remove_common_indent(s2.rstrip())
    eq_(ss1, ss2, msg='\n%s\n != \n%s' % (ss1, ss2))

