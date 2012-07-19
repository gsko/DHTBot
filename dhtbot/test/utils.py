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

    The original method will be called if it is supplied in the constructor

    """
    def __init__(self, orig_func=None):
        self.count = 0
        self.orig_func = orig_func

    def __call__(self, *args, **kwargs):
        self.count += 1
        if self.orig_func is not None:
            return self.orig_func(*args, **kwargs)

    def reset(self):
        self.count = 0


class HollowUDPTransport(object):
    """
    Mimic the write functionality of a UDP Transport
    """
    def __init__(self):
        self.packet = None
        self.address = None

    def write(self, packet, address):
        self.packet = packet
        self.address = address


class HollowDelayedCall(object):
    def active(self):
        return False

    def cancel(self):
        pass

class HollowReactor(object):
    def callLater(self, timeout, function, *args, **kwargs):
        return HollowDelayedCall()


