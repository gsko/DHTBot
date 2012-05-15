from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from dhtbot import rate_limiter, constants
from dhtbot.coding import krpc_coder
from dhtbot.krpc_types import Query
from dhtbot.rate_limiter import RateLimiter, TokenBucket
from dhtbot.test.utils import Clock


class TestingBase(object):
    def setUp(self):
        self.clock = Clock()
        self.monkey_patcher = MonkeyPatcher()
        self.monkey_patcher.addPatch(rate_limiter.time, "time", self.clock)
        self.monkey_patcher.patch()

    def tearDown(self):
        self.monkey_patcher.restore()

class RateLimiterTestCase(TestingBase, unittest.TestCase):
    def setUp(self):
        TestingBase.setUp(self)
        # Set up a query and address for testing
        self.address = ("127.0.0.1", 55)
        self.query = Query()
        self.query.rpctype = "ping"
        self.query._querier = 15
        self.query._transaction_id = 99
        self.packet = krpc_coder.encode(self.query)
        # Patch in hardcoded value for the bandwidth
        # limits so that changing the constants will
        # not effect the usefulness of this test case
        # (The global bandwidth is set to 3 standard ping queries)
        # (The per user bandwidth is set to 1 standard ping query)
        self.monkey_patcher.addPatch(rate_limiter.constants,
                                     "global_bandwidth_rate",
                                     3 * len(self.packet))
        self.monkey_patcher.addPatch(rate_limiter.constants,
                                     "host_bandwidth_rate",
                                     1 * len(self.packet))
        self.monkey_patcher.patch()


    def test_consume_enoughBW(self):
        rl = RateLimiter()
        consumed = rl.consume(self.packet, self.address)
        self.assertTrue(consumed)

    def test_consume_overflowHostAndReset(self):
        rl = RateLimiter()
        # Consume first packet
        consumed = rl.consume(self.packet, self.address)
        self.assertTrue(consumed)
        # Drop second packet
        consumed = rl.consume(self.packet, self.address)
        self.assertFalse(consumed)
        # Wait a second for the limiter to reset
        self.clock.set(1)
        # And consume a packet again
        consumed = rl.consume(self.packet, self.address)
        self.assertTrue(consumed)

    def test_consume_overflowGlobalAndReset(self):
        address1 = self.address
        address2 = ("127.0.0.1", 9999)
        address3 = ("127.0.0.1", 8888)
        address4 = ("127.0.0.1", 7777)
        rl = RateLimiter()
        # Consume first, second, and third packets
        consumed = rl.consume(self.packet, address1)
        self.assertTrue(consumed)
        consumed = rl.consume(self.packet, address2)
        self.assertTrue(consumed)
        consumed = rl.consume(self.packet, address3)
        self.assertTrue(consumed)
        # Drop the fourth
        consumed = rl.consume(self.packet, address4)
        self.assertFalse(consumed)
        # Wait a second for the limiter to reset
        self.clock.set(1)
        # And consume a packet again
        consumed = rl.consume(self.packet, address3)
        self.assertTrue(consumed)


class TokenBucketTestCase(TestingBase, unittest.TestCase):
    def test_can_consume_enoughTokens(self):
        tb = TokenBucket(10, 1)
        self.assertTrue(tb.can_consume(5))

    def test_can_consume_notEnoughTokens(self):
        tb = TokenBucket(10, 1)
        self.assertFalse(tb.can_consume(50))

    def test_can_consume_tokenRefill(self):
        tb = TokenBucket(10, 1)
        self.assertFalse(tb.can_consume(50))
        self.clock.set(40)
        self.assertFalse(tb.can_consume(50))

    def test_consume_verifyTokenDecrease(self):
        tb = TokenBucket(10, 1)
        self.assertTrue(tb.consume(10))
        self.assertEquals(0, tb.tokens)

    def test_consume_notEnoughTokens(self):
        tb = TokenBucket(10, 1)
        self.assertFalse(tb.consume(100))
        self.assertEquals(10, tb.tokens)
