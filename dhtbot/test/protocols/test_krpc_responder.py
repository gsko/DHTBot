from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from dhtbot import constants, contact
from dhtbot.coding import krpc_coder
from dhtbot.krpc_types import Query, Response
from dhtbot.protocols import krpc_responder, krpc_sender
from dhtbot.protocols.krpc_responder import KRPC_Responder, _TokenGenerator
from dhtbot.test.protocols.test_krpc_sender import (HollowTransport,
        HollowReactor)

monkey_patcher = MonkeyPatcher()

class Clock(object):
    def __init__(self):
        self._time = 0

    def set(self, time):
        self._time = time

    def time(self):
        return self._time

class SendResponseWrapper(object):
    def __init__(self, sendResponse):
        self.sendResponse = sendResponse

    def __call__(self, response, address):
        self.sendResponse(response, address)
        self.response = response
        self.address = address

test_address = ("127.0.0.1", 8888)

class KRPC_ResponderTestCase(unittest.TestCase):
    def setUp(self):
        monkey_patcher.addPatch(krpc_sender, "reactor", HollowReactor())
        monkey_patcher.patch()

    def tearDown(self):
        monkey_patcher.restore()

    def _patched_responder(self, node_id=None):
        kresponder = KRPC_Responder(node_id=node_id)
        kresponder.transport = HollowTransport()
        kresponder.sendResponse = SendResponseWrapper(kresponder.sendResponse)
        return kresponder

    def _compare_responses(self, expected, actual, attributes=None):
        # Always check these attributes
        _attrs = ["_transaction_id", "_from"]

        # Prepare a list of attributes to check
        if attributes is None:
            attributes = _attrs
        else:
            attributes = _attrs + attributes

        for attribute in attributes:
            expected_val = getattr(expected, attribute)
            actual_val = getattr(actual, attribute)
            self.assertEquals(expected_val, actual_val)

    def test_ping_Received_sendsValidResponse(self):
        kresponder = self._patched_responder()
        incoming_query = Query()
        incoming_query.rpctype = "ping"
        incoming_query._from = 123
        incoming_query._transaction_id = 15
        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = 15
        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        self._compare_responses(expected_response, actual_response)

    def test_find_node_Received_sendsValidResponseMultipleNodes(self):
        # Create the protocol and populate its
        # routing table with nodes
        kresponder = self._patched_responder()
        node_list = []
        node_gen = lambda num: contact.Node(num, ("127.0.0.%d" % num, num))
        for i in range(100):
            n = node_gen(i)
            if kresponder.routing_table.offer_node(n):
                node_list.append(n)

        querying_node = contact.Node(123, test_address)
        incoming_query = Query()
        incoming_query.rpctype = "find_node"
        incoming_query._from = querying_node.node_id
        incoming_query._transaction_id = 15
        incoming_query.target_id = 777777

        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = 15
        node_list.sort(key = lambda node:
                        node.distance(incoming_query.target_id))
        node_list = node_list[:constants.k]
        expected_response.nodes = node_list

        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        self._compare_responses(expected_response,
                                actual_response, ["nodes"])

    def test_find_node_Received_sendsValidResponseWithTargetNode(self):
        # Create the protocol and populate its
        # routing table with nodes
        # We need a node_id of 75 so that our kbuckets split
        # in a way that we will have the target node of 77
        kresponder = self._patched_responder(75)
        node_list = []
        node_gen = lambda num: contact.Node(num, ("127.0.0.%d" % num, num))
        for i in range(100):
            n = node_gen(i)
            if kresponder.routing_table.offer_node(n):
                node_list.append(n)

        querying_node = contact.Node(123, test_address)
        incoming_query = Query()
        incoming_query.rpctype = "find_node"
        incoming_query._from = querying_node.node_id
        incoming_query._transaction_id = 15
        # We have this target id in our routing table
        incoming_query.target_id = 77

        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = 15
        node_list.sort(key = lambda node:
                        node.distance(incoming_query.target_id))
        node_list = node_list[:1]
        expected_response.nodes = node_list

        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        self._compare_responses(expected_response,
                                actual_response, ["nodes"])
    
    def test_get_peers_Received_sendsValidResponseWithNodes(self):
        # Create the protocol and populate its
        # routing table with nodes
        # We need a node_id of 75 so that our kbuckets split
        # in a way that we will have the target node of 77
        kresponder = self._patched_responder(75)
        node_list = []
        node_gen = lambda num: contact.Node(num, ("127.0.0.%d" % num, num))
        for i in range(100):
            n = node_gen(i)
            if kresponder.routing_table.offer_node(n):
                node_list.append(n)

        # simulate that a get_peers query has been
        # received by making a fake get_peers query
        # and feeding it into "datagramReceived()"
        querying_node = contact.Node(123, test_address)
        incoming_query = Query()
        incoming_query.rpctype = "get_peers"
        incoming_query._from = querying_node.node_id
        incoming_query._transaction_id = 15
        # We have this target id in our routing table
        incoming_query.target_id = 77

        # Create a response object and ensure
        # and the response (that the node sends)
        # matches what we made
        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = 15
        # the specification calls for the resulting
        # nodes to be sorted by distance
        node_list.sort(key = lambda node:
                        node.distance(incoming_query.target_id))
        node_list = node_list[:constants.k]
        expected_response.nodes = node_list

        # simulating the incoming query and capture
        # the outgoing response
        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        self._compare_responses(expected_response,
                                actual_response, ["nodes", "peers"])

    def test_get_peers_Received_sendsValidResponseWithPeers(self):
        # Create the protocol and populate its
        # routing table with nodes
        kresponder = self._patched_responder()
        peers = [("127.0.0.%d" % peer_num, peer_num) for
                                        peer_num in range(10)]
        incoming_query = Query()
        incoming_query.rpctype = "get_peers"
        incoming_query._from = 555
        incoming_query._transaction_id = 15
        # We have this target id in our routing table
        incoming_query.target_id = 77

        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = 15
        expected_response.peers = peers

        for peer in peers:
            kresponder._datastore.put(incoming_query.target_id, peer)
        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        actual_response.peers.sort(key = lambda (ip, port) : port)
        self._compare_responses(expected_response,
                                actual_response, ["nodes", "peers"])

    def test_announce_peer_Received_sendsValidResponse(self):
        kresponder = self._patched_responder()
        # announce_peer queries need a token (the token value
        # comes in response to a get_peers query)
        # So first, we need to "receive" a get_peers query

        # get_peers creation and "receiving"
        query = Query()
        query.rpctype = "get_peers"
        query._from = 123
        query._transaction_id = 150
        query.target_id = 800
        kresponder.datagramReceived(krpc_coder.encode(query),
                                    test_address)
        response = kresponder.sendResponse.response
        # announce_peer creation and "receiving"
        incoming_query = Query()
        incoming_query._transaction_id = 999
        incoming_query._from = query._from
        incoming_query.rpctype = "announce_peer"
        incoming_query.token = response.token
        incoming_query.port = 55
        incoming_query.target_id = query.target_id

        # Test the announce_peer response
        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = incoming_query._transaction_id
        # Reset the response grabber
        kresponder.sendResponse.response = None
        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        self._compare_responses(expected_response, actual_response)

    def test_announce_peer_Received_validTokenAddsPeer(self):
        kresponder = self._patched_responder()
        # announce_peer queries need a token (the token value
        # comes in response to a get_peers query)
        # So first, we need to "receive" a get_peers query

        # get_peers creation and "receiving"
        query = Query()
        query.rpctype = "get_peers"
        query._from = 123
        query._transaction_id = 150
        query.target_id = 800
        kresponder.datagramReceived(krpc_coder.encode(query),
                                    test_address)
        response = kresponder.sendResponse.response
        # announce_peer creation and "receiving"
        incoming_query = Query()
        incoming_query._transaction_id = 999
        incoming_query._from = query._from
        incoming_query.rpctype = "announce_peer"
        incoming_query.token = response.token
        incoming_query.port = 55
        incoming_query.target_id = query.target_id

        # Test the announce_peer response
        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = incoming_query._transaction_id
        # Reset the response grabber
        kresponder.sendResponse.response = None
        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        self._compare_responses(expected_response, actual_response)

        # Check to see if another get_peers query will return us
        # as a peer
        query = Query()
        query.rpctype = "get_peers"
        query._from = 123
        query._transaction_id = 9809831
        query.target_id = 800
        kresponder.datagramReceived(krpc_coder.encode(query),
                                    test_address)
        response = kresponder.sendResponse.response
        self.assertEquals(1, len(response.peers))
        test_ip, test_port = test_address
        returned_peer = response.peers[0]
        self.assertEquals((test_ip, incoming_query.port), returned_peer)

    def test_announce_peer_Received_invalidTokenDoesntAddPeer(self):
        kresponder = self._patched_responder()
        # announce_peer queries need a token (the token value
        # comes in response to a get_peers query)
        # So first, we need to "receive" a get_peers query

        # get_peers creation and "receiving"
        query = Query()
        query.rpctype = "get_peers"
        query._from = 123
        query._transaction_id = 150
        query.target_id = 800
        kresponder.datagramReceived(krpc_coder.encode(query),
                                    test_address)
        response = kresponder.sendResponse.response
        # announce_peer creation and "receiving"
        incoming_query = Query()
        incoming_query._transaction_id = 999
        incoming_query._from = query._from
        incoming_query.rpctype = "announce_peer"
        incoming_query.token = 5858585858 # this is an invalid token
        incoming_query.port = 55
        incoming_query.target_id = query.target_id

        # Test the announce_peer response
        expected_response = Response()
        expected_response._from = kresponder.node_id
        expected_response._transaction_id = incoming_query._transaction_id
        # Reset the response grabber
        kresponder.sendResponse.response = None
        kresponder.datagramReceived(krpc_coder.encode(incoming_query),
                                    test_address)
        actual_response = kresponder.sendResponse.response
        # Make sure we didnt send a response
        self.assertEquals(None, actual_response)

        # Check to see if another get_peers query will return us
        # as a peer
        query = Query()
        query.rpctype = "get_peers"
        query._from = 123
        query._transaction_id = 9809831
        query.target_id = 800
        kresponder.datagramReceived(krpc_coder.encode(query),
                                    test_address)
        response = kresponder.sendResponse.response
        # Make sure no peers were returned
        self.assertEquals(None, response.peers)

class QuarantinerTestCase(unittest.TestCase):
    # TODO
    pass

class NICER_TestCase(unittest.TestCase):
    # TODO
    pass

class _TokenGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        monkey_patcher.addPatch(krpc_responder, "time", self.clock)
        monkey_patcher.patch()
        self.address = ("127.0.0.1", 5555)
        # Attach a standard test query
        query = Query()
        query._from = 15125
        query.rpctype = "get_peers"
        query.target_id = 90809
        self.query = query
        # The token generator that will be tested
        self.tgen = _TokenGenerator()

    def tearDown(self):
        monkey_patcher.restore()

    def test_generate_sameQueryTwiceSameSecret(self):
        first_token = self.tgen.generate(self.query, self.address)
        second_token = self.tgen.generate(self.query, self.address)
        self.assertEqual(first_token, second_token)

    def test_generate_sameQueryDifferentSecrets(self):
        first_token = self.tgen.generate(self.query, self.address)
        # Force the token generator to make a new secret
        self.clock.set(constants._secret_timeout)
        second_token = self.tgen.generate(self.query, self.address)
        # TODO
        # it is possible that the hash values could collide
        # (one suggestion was to run 100 tests and test that
        #  atleast 99 succeeded)
        self.assertNotEqual(first_token, second_token)

    def test_verify_sameSecret(self):
        token = self.tgen.generate(self.query, self.address)
        self.clock.set(3)
        self.assertTrue(self.tgen.verify(self.query, self.address, token))

    def test_verify_newSecret(self):
        token = self.tgen.generate(self.query, self.address)
        self.clock.set(constants._secret_timeout)
        self.assertTrue(self.tgen.verify(self.query, self.address, token))

    def test_verify_tokenTimeout(self):
        token = self.tgen.generate(self.query, self.address)
        self.clock.set(constants.token_timeout - 1)
        self.assertTrue(self.tgen.verify(self.query, self.address, token))
        self.clock.set(constants.token_timeout)
        self.assertFalse(self.tgen.verify(self.query, self.address, token))
