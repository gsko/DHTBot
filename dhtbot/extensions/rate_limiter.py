"""
Simple rate limiting algorithms and auxilary data structures along with
a patcher for IKRPC_Sender implementations

"""
import time

from collections import defaultdict
from twisted.python.components import proxyForInterface

from dhtbot import constants
from dhtbot.protocols.krpc_sender import IKRPC_Sender
from dhtbot.coding import krpc_coder

class RateLimiter(object):
    """
    Determine whether a packet should be sent/received

    The RateLimiter keeps track of how much data has been received
    and sent from every host. If that amount is higher than
    the specified constant value, the RateLimiter will suggest
    that the packet be dropped

    @see dhtbot.constants.global_bandwidth_rate
    @see dhtbot.constants.host_bandwidth_rate

    """
    def __init__(self):
        self.global_bucket = TokenBucket(constants.global_bandwidth_rate,
                                         constants.global_bandwidth_rate)
        self.host_buckets = defaultdict(
                lambda: TokenBucket(constants.host_bandwidth_rate,
                                    constants.host_bandwidth_rate))

    def consume(self, packet, address):
        """
        Tells whether the given packet can be processed/sent

        @Returns boolean indicating whether the packet was "consumed"
        by the rate limiter. The packet will not be consumed if there
        was not enough bandwidth in the rate limiter

        """
        consumed = False
        packet_len = len(packet)
        host_bucket = self.host_buckets[address]

        enough_global_bw = self.global_bucket.can_consume(packet_len)
        enough_host_bw = host_bucket.can_consume(packet_len)
        if enough_global_bw and enough_host_bw:
            self.global_bucket.consume(len(packet))
            host_bucket.consume(len(packet))
            consumed = True
        return consumed

class TokenBucket(object):
    """An implementation of the token bucket algorithm.
    
    http://en.wikipedia.org/wiki/Token_bucket

    """
    # Original code found here:
    # http://code.activestate.com/recipes/511490-implementation-of-the-token-bucket-algorithm/
    # Note: changes have been made (Greg Skoczek, 26 April 2012)

    def __init__(self, tokens, fill_rate):
        """
        Create a token bucket of 'tokens' size that fills at 'fill_rate'

        @param tokens: the maximum amount of tokens that this
            token bucket can hold
        @param fill_rate: the rate at which tokens enter the token
            bucket (tokens / second)

        """
        self.capacity = tokens
        self._tokens = tokens
        self.fill_rate = fill_rate
        self.timestamp = time.time()

    def can_consume(self, tokens):
        """
        Tells whether there are atleast `tokens` tokens

        @returns: True/False

        """
        return tokens <= self.tokens

    def consume(self, tokens):
        """
        Consume tokens from the bucket.
        
        @returns: True if there were sufficient tokens otherwise False.
        
        """
        enough_tokens = self.can_consume(tokens)
        if enough_tokens:
            self._tokens -= tokens
        return enough_tokens

    @property
    def tokens(self):
        """
        Calculate the number of available tokens in the bucket

        @returns: the number of tokens in the token bucket (int)
        
        """
        if self._tokens < self.capacity:
            now = time.time()
            delta = long(round(self.fill_rate * (now - self.timestamp)))
            self._tokens = min(self.capacity, self._tokens + delta)
            self.timestamp = now
        return self._tokens


class RateLimiter_Patcher(proxyForInterface(IKRPC_Sender, '_original')):
    """
    Limits the rate at which queries can enter/exit a KRPC_Sender instance

    The object passed in to the constructor should implement
    IKRPC_Sender. The passed in object will be overridden in
    such a way that only a particular amount of bytes will
    be allowed to be received/sent at a time (on a global
    and per host limit)

    @see dhtbot.rate_limiter.RateLimiter
    @see dhtbot.constants.host_bandwidth_rate
    @see dhtbot.constants.global_bandwidth_rate

    """
    # TODO this method should not be needed, but
    # removing it causes weird errors
    def __init__(self, original):
        self._original = original

    def startProtocol(self):
        self._original.startProtocol()
        self._incoming_rate_limiter = RateLimiter()
        self._outgoing_rate_limiter = RateLimiter()

    def sendKRPC(self, krpc, address):
        encoded_krpc = krpc_coder.encode(krpc)
        enough_bandwidth_to_send = \
                self._outgoing_rate_limiter.consume(encoded_krpc, address)
        if enough_bandwidth_to_send:
            self._original.sendKRPC(krpc, address)

    def datagramReceived(self, datagram, address):
        # Only pass datagrams down the processing chain
        # if the rate limiter agrees
        enough_bandwidth_to_accept = \
                self._incoming_rate_limiter.consume(datagram, address)
        if enough_bandwidth_to_accept:
            self._original.datagramReceived(datagram, address)
