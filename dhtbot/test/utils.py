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


class Counter(object):
    """
    Replaces a method with a running counter of how many times it was called

    >>> import time
    >>> time.time = Counter()
    >>> time.time.count
    0
    >>> time.time()
    >>> time.time.count
    1
    >>> time.time.reset()
    >>> time.time.count
    0

    The original method is NOT called

    """
    def __init__(self):
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1

    def reset(self):
        self.count = 0
