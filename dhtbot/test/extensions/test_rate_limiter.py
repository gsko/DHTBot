from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from dhtbot.extensions import rate_limiter
from dhtbot.extensions.rate_limiter import RateLimiter, RateLimiter_Patcher
from dhtbot.coding import krpc_coder
from dhtbot.kademlia.routing_table import TreeRoutingTable
from dhtbot.krpc_types import Query
from dhtbot.protocols.krpc_sender import KRPC_Sender
from dhtbot.test.utils import Clock

# TODO refactor this HollowTransport with the one with dhtbot.test.utils
from dhtbot.test.protocols.test_krpc_sender import \
        HollowTransport, Clock, Counter

class RateLimiterTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.monkey_patcher = MonkeyPatcher()
        self.monkey_patcher.addPatch(rate_limiter.time, "time", self.clock)
        self.monkey_patcher.patch()
        self.address = ("127.0.0.1", 55)
        self.query = Query()
        self.query.rpctype = "ping"
        self.query._from = 15
        self.query._transaction_id = 99
        self.packet = krpc_coder.encode(self.query)
        # Patch in hardcoded value for the bandwidth
        # limits so that changing the constants will
        # not effect the usefulness of this test case
        # (The global bandwidth is set to 3 standard ping queries)
        # (The per user bandwidth is set to 1 standard ping query)
        self.monkey_patcher.addPatch(rate_limiter.constants,
                "global_bandwidth_rate", 3 * len(self.packet))
        self.monkey_patcher.addPatch(rate_limiter.constants,
                "host_bandwidth_rate", 1 * len(self.packet))
        self.monkey_patcher.patch()

    def tearDown(self):
        self.monkey_patcher.restore()

    def _patched_sender(self):
        ksender = KRPC_Sender(TreeRoutingTable, 2**50)
        ksender.transport = HollowTransport()
        # Start the protocol to simulate
        # a regular environment
        rate_limited_proto = RateLimiter_Patcher(ksender)
        rate_limited_proto.startProtocol()
        return rate_limited_proto

    def test_inbound_overflowHostAndReset(self):
        """
        Make sure that we cannot overflow our inbound host bandwidth limit

        @see dhtbot.constants.host_bandwidth_rate

        """
        rate_limited_proto = self._patched_sender()
        counter = Counter()
        counter.num = 0
        rate_limited_proto.krpcReceived = counter.count
        # One packet should be accepted without problems
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), self.address)
        self.assertEquals(1, counter.num)
        counter.num = 0
        # The second packet should be dropped
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), self.address)
        self.assertEquals(0, counter.num)
        # Reset the rate limiter and the next packet should
        # be accepted
        self.clock.set(1)
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), self.address)
        self.assertEquals(1, counter.num)

    def test_inbound_overflowGlobalAndReset(self):
        """
        Make sure that we cannot overflow our inbound global bandwidth limit

        @see dhtbot.constants.host_global_rate

        """
        address1 = ("127.0.0.1", 66)
        address2 = ("127.0.0.1", 76)
        address3 = ("127.0.0.1", 86)
        address4 = ("127.0.0.1", 555)
        rate_limited_proto = self._patched_sender()
        counter = Counter()
        counter.num = 0
        rate_limited_proto.krpcReceived = counter.count
        # The first three packets should be accepted without
        # any problems
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), address1)
        self.assertEquals(1, counter.num)
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), address2)
        self.assertEquals(2, counter.num)
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), address3)
        self.assertEquals(3, counter.num)
        # The fourth packet should be dropped
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), address4)
        self.assertEquals(3, counter.num)
        # Reset the rate limiter and the next packet should be
        # accepted
        self.clock.set(1)
        rate_limited_proto.datagramReceived(
                krpc_coder.encode(self.query), self.address)
        self.assertEquals(4, counter.num)

    def test_outbound_overflowHostAndReset(self):
        """
        Make sure that we cannot overflow our outbound host bandwidth limit

        @see dhtbot.constants.host_bandwidth_rate

        """
        rate_limited_proto = self._patched_sender()
        # The first packet should go through without any problems
        rate_limited_proto.sendKRPC(self.query, self.address)
        self.assertTrue(
                rate_limited_proto._original.transport._packet_was_sent())
        # Second packet should not go through
        rate_limited_proto.sendKRPC(self.query, self.address)
        self.assertFalse(
                rate_limited_proto._original.transport._packet_was_sent())
        # Update the clock (reseting the rate limiter)
        self.clock.set(1)
        # This packet should now go through)
        rate_limited_proto.sendKRPC(self.query, self.address)
        self.assertTrue(
                rate_limited_proto._original.transport._packet_was_sent())

    def test_outbound_overflowGlobalAndReset(self):
        """
        Make sure that we cannot overflow our outbound global bandwidth limit

        @see dhtbot.constants.global_bandwidth_rate

        """
        rate_limited_proto = self._patched_sender()
        # Reset the hollow transport
        rate_limited_proto._original.transport._reset()
        # The first three packets should go through without any problems
        address1 = ("127.0.0.1", 66)
        address2 = ("127.0.0.1", 76)
        address3 = ("127.0.0.1", 86)
        address4 = ("127.0.0.1", 555)

        # Packet 1, 2, 3
        for i in range(1, 4):
            rate_limited_proto.sendKRPC(
                    self.query, locals()['address' + str(i)])
            self.assertTrue(
                    rate_limited_proto._original.transport._packet_was_sent())

        # The fourth packet should not go through
        rate_limited_proto.sendKRPC(self.query, address4)
        self.assertFalse(
                rate_limited_proto._original.transport._packet_was_sent())
        # Change the time to reset the rate limiter
        self.clock.set(1)
        # This packet should now go through
        rate_limited_proto.sendKRPC(self.query, self.address)
        self.assertTrue(
                rate_limited_proto._original.transport._packet_was_sent())
