from singlechar_fwrap import *
import numpy as np

__doc__ = """
    >>> singlechar('A', 'a')
    ('b', 'B')
    >>> singlechar('A', 'ab')
    Traceback (most recent call last):
        ...
    ValueError: len(y) != 1

    >>> singlechar(u'A', u'a')
    ('b', 'B')

    >>> singlechar(u'A', ord('a'))
    ('b', 'B')
    
"""
