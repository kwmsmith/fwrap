from all_char_fwrap import *

__doc__ = u'''
>>> char_arg('foobar', 'ch_in')
('ch_in               ', 'ch_in')
>>> char_star('aaaaa', 'bb', 'cccccccccc', 'dddddddd')
('bb   ', 'dddddddd  ', 'dddddddd')
>>> char1("1234567890")
'aoeuidhtns          '
>>> char2("1234567890")
>>> char3()
"',.py"
>>> char4("a")
'^'
>>> char_len_x(ch='a'*20, ch_in='b'*10, ch_inout='_')
('bbbbbbbbbb_bbbb_bbbb', '_bbbb', 'a')
>>> len_1_args('a', 'b')
('b', 'b', 'b')
'''
