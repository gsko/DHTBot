from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from dhtbot.krpc_types import (Query, Response, Error)
from dhtbot.kademlia.routing_table import TreeRoutingTable
from dhtbot.protocols import krpc_sender
from dhtbot.protocols.krpc_sender import KRPC_Sender, KRPCRateLimiter
from dhtbot.protocols.errors import TimeoutError
from dhtbot.coding import krpc_coder
from dhtbot.test.utils import Clock
from dhtbot import rate_limiter

class HollowTransport(object):
    def __init__(self):
        self.data = None
        self.address = None

    def write(self, data, address):
        """
        Remember what data and address was passed into write and do nothing
        """
        self.data = data
        self.address = address

    def _reset(self):
        """
        Resets the HollowTransport so that it appears as if no packet was sent
        """
        self.data = None
        self.address = None

    def _packet_was_sent(self):
        """
        Check whether a packet has been sent

        In either case, reset the HollowTransport to appear as if
        no packets have been sent

        """
        sent = self.data != None and self.address != None
        self._reset()
        return sent

class HollowDelayedCall(object):
    def active(self):
        return False

    def cancel(self):
        pass

class HollowReactor(object):
    def callLater(self, timeout, function, *args, **kwargs):
        return HollowDelayedCall()

class Counter(object):
    def __init__(self):
        self.num = 0

    def count(self, *args, **kwargs):
        self.num += 1

# Write two functions that simply remove / restore
# the reactor for krpc_sender
monkey_patcher = MonkeyPatcher()

def _swap_out_reactor():
    monkey_patcher.addPatch(krpc_sender, "reactor", HollowReactor())
    monkey_patcher.patch()

def _restore_reactor():
    monkey_patcher.restore()

# Arguments for the sendQuery
timeout = 15
address = ("127.0.0.1", 2828)

class KRPC_Sender_ReceivedCallChainTestCase(unittest.TestCase):
    def _patch_counter_and_input_krpc(self, krpc, method_name,
                                      num_calls=1, address=None):
        if address is None:
            address = ("127.0.0.1", 8888)
        k_messenger = KRPC_Sender(TreeRoutingTable, 2**50)
        # Patch in our counter
        counter = Counter()
        setattr(k_messenger, method_name, counter.count)
        # Pass in the krpc
        k_messenger.datagramReceived(krpc_coder.encode(krpc), address)
        self.assertEquals(num_calls, counter.num)

    def setUp(self):
        _swap_out_reactor()

    def tearDown(self):
        _restore_reactor()

    def test_krpcReceived(self):
        query = Query()
        query._transaction_id = 50
        query._querier = 58
        query.rpctype = "ping"
        self._patch_counter_and_input_krpc(query, "krpcReceived")

    def test_queryReceived(self):
        query = Query()
        query._transaction_id = 50
        query._querier = 58
        query.rpctype = "ping"
        self._patch_counter_and_input_krpc(query, "queryReceived")

    def test_ping_Received(self):
        query = Query()
        query._transaction_id = 50
        query._querier = 58
        query.rpctype = "ping"
        self._patch_counter_and_input_krpc(query, query.rpctype + "_Received")

    def test_find_node_Received(self):
        query = Query()
        query._transaction_id = 50
        query._querier = 58
        query.rpctype = "find_node"
        query.target_id = 1500
        self._patch_counter_and_input_krpc(query, query.rpctype + "_Received")

    def test_get_peers_Received(self):
        query = Query()
        query._transaction_id = 50
        query._querier = 58
        query.rpctype = "get_peers"
        query.target_id = 1500
        self._patch_counter_and_input_krpc(query, query.rpctype + "_Received")

    def test_announce_peer_Received(self):
        query = Query()
        query._transaction_id = 50
        query._querier = 58
        query.rpctype = "announce_peer"
        query.target_id = 1500
        query.port = 5125
        query.token = 15
        self._patch_counter_and_input_krpc(query, query.rpctype + "_Received")

    def test_responseReceived(self):
        # Make a query that we will "send"
        query = Query()
        query.rpctype = "ping"
        # Make the protocol and patch in our counter, transport, and reactor
        counter = Counter()
        k_messenger = KRPC_Sender(TreeRoutingTable, 2**50)
        k_messenger.transport = HollowTransport()
        k_messenger.responseReceived = counter.count
        # Send the query and receive the response
        k_messenger.sendQuery(query, address, timeout)
        self.assertTrue(query._transaction_id in k_messenger._transactions)
        # Make a response that we will "receive"
        response = query.build_response()
        response._queried = 9
        k_messenger.datagramReceived(krpc_coder.encode(response), address)
        _restore_reactor()
        self.assertEquals(1, counter.num)

class KRPC_Sender_DeferredTestCase(unittest.TestCase):
    def setUp(self):
        _swap_out_reactor()
        self.k_messenger = KRPC_Sender(TreeRoutingTable, 2**50)
        self.k_messenger.transport = HollowTransport()
        self.query = Query()
        self.query.rpctype = "ping"

    def tearDown(self):
        _restore_reactor()

    def _response_equality(self, response, expected_response):
            self.assertEquals(expected_response._transaction_id,
                              response._transaction_id)
            self.assertEquals(expected_response._queried,
                              response._queried)
            return response

    def test_callback(self):
        counter = Counter()
        d = self.k_messenger.sendQuery(self.query, address, timeout)
        self.assertTrue(self.query._transaction_id in
                        self.k_messenger._transactions)
        # Build the response we will "receive"
        response = self.query.build_response()
        response._queried = 9
        d.addCallback(self._response_equality, response)
        d.addCallback(counter.count)
        encoded_response = krpc_coder.encode(response)
        self.k_messenger.datagramReceived(encoded_response, address)
        self.assertEquals(1, counter.num)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

    def _error_equality(self, error, expected_error):
                self.assertEquals(expected_error._transaction_id,
                                  error._transaction_id)
                self.assertEquals(expected_error.code, error.code)
                return error 

    def test_errback_KRPCError(self):
        counter = Counter()
        d = self.k_messenger.sendQuery(self.query, address, timeout)
        self.assertTrue(self.query._transaction_id in
                        self.k_messenger._transactions)
        # Build the response we will "receive"
        error = self.query.build_error()
        d.addErrback(self._error_equality, error)
        d.addErrback(counter.count)
        encoded_error = krpc_coder.encode(error)
        self.k_messenger.datagramReceived(encoded_error, address)
        self.assertEquals(1, counter.num)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

    def _neutralize_invalidKRPCError(self, failure):
        failure.trap(krpc_coder.InvalidKRPCError)

    def test_errback_InvalidKRPCError(self):
        # Make an invalid query
        query = Query()
        query.rpctype = "pingpong"
        d = self.k_messenger.sendQuery(query, address, timeout)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)
        counter = Counter()
        d.addErrback(self._neutralize_invalidKRPCError)
        d.addErrback(counter.count)
        self.assertEquals(0, counter.num)

    def _neutralize_TimeoutError(self, failure):
        failure.trap(TimeoutError)

    def test_errback_TimeoutError(self):
        counter = Counter()
        d = self.k_messenger.sendQuery(self.query, address, timeout)
        self.assertTrue(self.query._transaction_id in
                        self.k_messenger._transactions)
        d.errback(TimeoutError())
        d.addErrback(self._neutralize_TimeoutError)
        d.addErrback(counter.count)
        self.assertEquals(0, counter.num)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

class KRPCRateLimiterTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.monkey_patcher = MonkeyPatcher()
        self.monkey_patcher.addPatch(rate_limiter.time, "time", self.clock)
        self.monkey_patcher.patch()
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
        rate_limited_proto = KRPCRateLimiter(ksender)
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
        # Packet 1
        rate_limited_proto.sendKRPC(self.query, address1)
        self.assertTrue(
                rate_limited_proto._original.transport._packet_was_sent())
        # Packet 2
        rate_limited_proto.sendKRPC(self.query, address2)
        self.assertTrue(
                rate_limited_proto._original.transport._packet_was_sent())
        # Packet 3
        rate_limited_proto.sendKRPC(self.query, address3)
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
