#!/usr/bin/env python2.4
# This program shows off a python decorator(which implements tail call
# optimization. It does this by throwing an exception if it is its own
# grandparent, and catching such exceptions to recall the stack.

# Original source: http://code.activestate.com/recipes/474088/
# License: PSF

import sys


class TailRecurseException:
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def tail_call_optimized(function):
    """
    This function decorates a function with tail call optimization. It does
    this by throwing an exception if it is its own grandparent, and catching
    such exceptions to fake the tail call optimization.

    This function fails if the decorated function recurses in a non-tail
    context.
    """
    def wrapper(*args, **kwargs):
        frame = sys._getframe()

        if frame.f_back and frame.f_back.f_back and \
                                    frame.f_back.f_back.f_code == frame.f_code:
            raise TailRecurseException(args, kwargs)
        else:
            while True:
                try:
                    return function(*args, **kwargs)
                except TailRecurseException, err:
                    args = err.args
                    kwargs = err.kwargs

    wrapper.__doc__ = function.__doc__

    return wrapper
