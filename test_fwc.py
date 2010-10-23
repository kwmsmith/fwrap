from fwc import subargs_split

from nose.tools import eq_, assert_raises

def test_subargs_split():
    argv = ['opt1', 'opt2', 'opt 3', 'foo', 'bar', 'bar 1', 'bar 2', 'baz']
    sbcmds = ('foo', 'bar', 'baz')
    output = {
            '' : argv[:3],
            'foo' : [],
            'bar' : ['bar 1', 'bar 2'],
            'baz' : []
            }

    eq_(output, subargs_split(sbcmds, argv))

    #FIXME: duplicate sbcmds on cmdline should raise error.

def test_duplicate():
    argv = ['bar', '1', 'foo', '2', 'bar']
    sbcmds = ('bar', 'foo')
    assert_raises(ValueError, subargs_split, sbcmds, argv)
