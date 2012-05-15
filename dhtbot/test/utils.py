"""
Various classes/functions commonly used in testing this package
"""
class Clock(object):
    """
    A drop in replacement for the time.time function

    >>> import time
    >>> time.time = Clock()
    >>> time.time()
    0
    >>> time.time.set(5)
    >>> time.time()
    5
    >>> 

    """
    def __init__(self):
        self._time = 0

    def __call__(self):
        return self.time()

    def time(self):
        return self._time

    def set(self, time):
        self._time = time
