from explicit_shape_fwrap import *
import numpy as np


__doc__ = u'''
    >>> arr = np.arange(10, dtype=np.int32)
    >>> explicit_shape_sum_1d(10, arr)
    45
    >>> explicit_shape_sum_1d(5, arr)
    10
    >>> explicit_shape_sum_1d(11, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_1d' wrapper.
    >>> explicit_shape_sum_1d(-1, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_1d' wrapper.

    >>> arr = np.arange(100, dtype=np.int32).reshape(10, 10)
    >>> explicit_shape_sum_2d(10, 10, arr)
    4950
    >>> explicit_shape_sum_2d(5, 10, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_2d' wrapper.
    >>> explicit_shape_sum_2d(10, 11, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_2d' wrapper.
    >>> explicit_shape_sum_2d(11, 10, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_2d' wrapper.
    >>> explicit_shape_sum_2d(10, -1, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_2d' wrapper.
    >>> explicit_shape_sum_2d(-1, 10, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_2d' wrapper.
    >>> explicit_shape_sum_2d(-1, 5, arr)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'explicit_shape_sum_2d' wrapper.

'''
