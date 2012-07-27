import pickle

from twisted.trial import unittest
from twisted.internet import defer

from dhtbot.krpc_types import Query
from dhtbot.xml_rpc.server_service import (KRPC_Sender_Server,
        KRPC_Responder_Server, KRPC_Iterator_Server)


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
        self.args = ()
        self.called = None

    ## KRPC_Sender
    #

    def sendQuery(self, query, address, timeout=None):
        self.args = (query, address, timeout)
        self.called = self.sendQuery
        return defer.Deferred()

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

    def setUp(self):
        self.node = Hollow_KRPC_Iterator()

class KRPC_Sender_Server_TestCase(unittest.TestCase, ServerTestCaseBase):
    """
    This test case ensures that the KRPC_Sender_Server
    properly passes all of its arguments to the
    underlying node protocol

    """
    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.kserver = KRPC_Sender_Server(self.node)
        q = Query()
        q.rpctype = "ping"
        q._from = 42
        self.test_query = q

    def test_sendQuery_args(self):
        self.kserver.xmlrpc_sendQuery(pickle.dumps(self.test_query),
                list(self.test_address), 55)
        expected_args = (self.test_query, self.test_address, 55)
        self.assertEquals(expected_args, self.node.args)
        self.assertEquals(self.node.called, self.node.sendQuery)


class KRPC_Responder_Server_TestCase(unittest.TestCase, ServerTestCaseBase):
    """Same as KRPC_Sender_Server_TestCase, but for KRPC_Responder Server"""

    def setUp(self):
        ServerTestCaseBase.setUp(self)
        self.kserver = KRPC_Responder_Server(self.node)

    def test_ping_args(self):
        self.kserver.xmlrpc_ping(list(self.test_address), timeout=123)
        expected_args = (self.test_address, 123)
        self.assertEquals(expected_args, self.node.args)
        self.assertEquals(self.node.called, self.node.ping)

    def test_find_node_args(self):
        #self.kserver.xmlrpc_find_node(list(self.test_address),
                #str(self.test_target_id))
        pass

    def test_get_peers_args(self):
        pass

    def test_announce_peer_args(self):
        pass

