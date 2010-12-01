from pyf_support_fwrap import *

#
# Check that the 4 arguments (see pyf_support.f)
# are turned into 2
#


__doc__ = u"""
    >>> m, n = 2, 4
    >>> testone(m, n)
    array([[  0.,   1.,   2.,   3.],
           [  4.,   5.,   6.,   7.],
           [  8.,   9.,  10.,  11.]])
    >>> testone(m)
    array([[ 0.,  1.],
           [ 2.,  3.],
           [ 4.,  5.]])

    >>> testone(10, n) # m_hidden == m+1
    Traceback (most recent call last):
        ...
    ValueError: Condition on arguments not satisfied: (m >= 1) and (m_hidden <= 10)

    >>> reorders(1, 3, np.arange(4).astype(np.int32))
    (3, 1, array([2, 2, 2, 2], dtype=int32))

    >>> r = np.arange(10)
    >>> fort_sum_simple(r, 10)
    45.0
    >>> fort_sum_simple(r)
    45.0
    >>> fort_sum_simple(r, 5)
    10.0
    
    >>> fort_sum_simple(r, -1)
    Traceback (most recent call last):
    ...
    RuntimeError: an error was encountered when calling the 'fort_sum_simple' wrapper.
    >>> fort_sum_simple(r, 11)
    Traceback (most recent call last):
    ...
    RuntimeError: an error was encountered when calling the 'fort_sum_simple' wrapper.

    
    >>> fort_sum(r)
    45.0
    >>> fort_sum(r, 10)
    45.0
    >>> fort_sum(r, 10, 0)
    45.0
    >>> fort_sum(r, 10, -1)
    Traceback (most recent call last):
        ...
    ValueError: Condition on arguments not satisfied: offx >= 0 and offx < np.PyArray_DIMS(arr)[0]
    >>> fort_sum(r, 10, 11)
    Traceback (most recent call last):
        ...
    ValueError: Condition on arguments not satisfied: offx >= 0 and offx < np.PyArray_DIMS(arr)[0]
    
Test offx argument::

    >>> fort_sum(r, 5, 5)
    35.0
    >>> fort_sum(r, 5, 6)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'fort_sum' wrapper.
    >>> fort_sum(r, 0, 9)
    0.0
    >>> fort_sum(r, 1, 9)
    9.0
    >>> fort_sum(r, 2, 9)
    Traceback (most recent call last):
        ...
    RuntimeError: an error was encountered when calling the 'fort_sum' wrapper.


    >>> fort_sum(r, offx=5)
    35.0
    >>> fort_sum(r, offx=9)
    9.0


"""
