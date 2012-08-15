import pickle

from twisted.trial import unittest
from twisted.internet import defer

from dhtbot.krpc_types import Query
from dhtbot.contact import Node
from dhtbot.xml_rpc.server_service import \
        KRPC_Responder_Server, KRPC_Iterator_Server

class Hollow_KRPC_Iterator(object):
    """
    Simple class that implements all KRPC_Iterator methods
    and dumps all collected arguments with each call

    ie:

    >>> hk = Hollow_KRPC_Iterator()
    >>> hk.find_iterate(42)
    >>> hk.args
    (42, None, None)
    >>> hk.called == hk.find_iterate
    True
    >>> 

    """
    def __init__(self, *args):
        assert 0 <= len(args) <= 2
        self.args = None
        self.called = None

    #
    #

    ## KRPC_Responder
    #

    def ping(self, address, timeout=None):
        self.args = (address, timeout)
        self.called = self.ping
        return defer.Deferred()

    def find_node(self, address, node_id, timeout=None):
        self.args = (address, node_id, timeout)
        self.called = self.find_node
        return defer.Deferred()

    def get_peers(self, address, target_id, timeout=None):
        self.args = (address, target_id, timeout)
        self.called = self.get_peers
        return defer.Deferred()

    def announce_peer(self, address, target_id, token, port, timeout=None):
        self.args = (address, target_id, token, port, timeout)
        self.called = self.announce_peer
        return defer.Deferred()

    #
    #

    ## KRPC_Iterator
    #

    def find_iterate(self, target_id, nodes=None, timeout=None):
        self.args = (target_id, nodes, timeout)
        self.called = self.find_iterate
        return defer.Deferred()

    def get_iterate(self, target_id, nodes=None, timeout=None):
        self.args = (target_id, nodes, timeout)
        self.called = self.get_iterate
        return defer.Deferred()

class ServerTestCaseBase(object):
    test_address = ("127.0.0.2", 22)
    test_target_id = 1234567890
    test_timeout = 588585

    def setUp(self):
        self.node = Hollow_KRPC_Iterator()

    def _check_node(self, expected_args, func):
        self.assertEquals(func, self.node.called)
        self.assertEquals(expected_args, self.node.args)
        # Reset to prevent false-positives / nonsensical-negatives
        self.node.called = None
        self.node.args = None

class KRPC_Responder_Server_TestCase(unittest.TestCase, ServerTestCaseBase):
    """
    Ensure the the server properly decodes and passes arguments

    """
    test_token = 12344321
    test_port = 2222

    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.kserver = KRPC_Responder_Server(self.node)

    def test_ping_args(self):
        args = (self.test_address, self.test_timeout)
        self.kserver.xmlrpc_ping(*map(pickle.dumps, args))
        self._check_node(args, self.node.ping)

    def test_find_node_args(self):
        args = (self.test_address, self.test_target_id, self.test_timeout)
        self.kserver.xmlrpc_find_node(*map(pickle.dumps, args))
        self._check_node(args, self.node.find_node)

    def test_get_peers_args(self):
        args = (self.test_address, self.test_target_id, self.test_timeout)
        self.kserver.xmlrpc_get_peers(*map(pickle.dumps, args))
        self._check_node(args, self.node.get_peers)

    def test_announce_peer_args(self):
        args = (self.test_address, self.test_target_id,
            self.test_token, self.test_port, self.test_timeout)
        self.kserver.xmlrpc_announce_peer(*map(pickle.dumps, args))
        self._check_node(args, self.node.announce_peer)

class KRPC_Iterator_Server_TestCase(unittest.TestCase, ServerTestCaseBase):

    test_nodes = [Node(num, ("127.0.0.%d" % num, num)) for num in xrange(2, 22)]

    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.kserver = KRPC_Iterator_Server(self.node)

    def test_find_iterate_args(self):
        self._test_iterate_args(self.kserver.xmlrpc_find_iterate,
            self.node.find_iterate)

    def test_get_iterate_args(self):
        self._test_iterate_args(self.kserver.xmlrpc_get_iterate,
            self.node.get_iterate)

    def _test_iterate_args(self, xml_func, node_func):
        args = (self.test_target_id, self.test_nodes, self.test_timeout)
        xml_func(*map(pickle.dumps, args))
        self._check_node(args, node_func)
