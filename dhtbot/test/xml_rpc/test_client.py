import pickle
import StringIO

from twisted.web import xmlrpc, server
from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.python.monkey import MonkeyPatcher

from dhtbot import constants, xml_rpc
from dhtbot.contact import Node
from dhtbot.xml_rpc.client import KRPC_Responder_Client, KRPC_Iterator_Client
from dhtbot.krpc_types import Query

monkey_patcher = MonkeyPatcher()

class HollowXMLRPCServer(object):
    """
    This "server" can be used to
    collect all outbound xml rpc client arguments.

    (Hint: monkey patch this class over
    'ServerProxy' attribute of xmlrpclib for the
    dhtbot.xml_rpc.client module and compare the
    outbound arguments to those that you expected)

    """
    def __init__(self, *args, **kwargs):
        pass

    def ping(self, p_address, p_timeout=None):
        p_args = (p_address, p_timeout)
        return self._prepare_args(p_args)

    def find_node(self, p_address, p_target_id, p_timeout=None):
        p_args = (p_address, p_target_id, p_timeout)
        return self._prepare_args(p_args)

    def get_peers(self, p_address, p_target_id, p_timeout=None):
        p_args = (p_address, p_target_id, p_timeout)
        return self._prepare_args(p_args)

    def announce_peer(self, p_address, p_target_id,
            p_token, p_port, p_timeout=None):
        p_args = (p_address, p_target_id, p_token, p_port, p_timeout)
        return self._prepare_args(p_args)

    def find_iterate(self, p_target_id, p_nodes=None, p_timeout=None):
        return self._iterate(p_target_id, p_nodes, p_timeout)

    def get_iterate(self, p_target_id, p_nodes=None, p_timeout=None):
        return self._iterate(p_target_id, p_nodes, p_timeout)

    def _prepare_args(self, p_args):
        return pickle.dumps(tuple(pickle.loads(p_arg) for p_arg in p_args))

    def _iterate(self, p_target_id, p_nodes, p_timeout):
        p_args = (p_target_id, p_nodes, p_timeout)
        return self._prepare_args(p_args)


class ClientTestBase(object):
    """
    Ensure the client passes valid arguments to the server
    """

    test_address = ("127.0.0.1", 58585)
    test_timeout = 15

    def setUp(self):
        self.monkey_patcher = mp = MonkeyPatcher()
        mp.addPatch(xml_rpc.client.xmlrpclib,
                    "ServerProxy", HollowXMLRPCServer)
        mp.patch()

    def tearDown(self):
        self.monkey_patcher.restore()

    def _check_args(self, args, func):
        """
        Make sure that the client sends the arguments in the proper format
        """
        # This loop is used in place of a simple 1-assert
        # to take into account None values that are passed through
        for arg, processed_arg in zip(args, func(*args)):
            self.assertEquals(arg, processed_arg)


class KRPC_Responder_Client_TestCase(ClientTestBase, unittest.TestCase):
    """
    These cases test for whether the XML RPC client passes
    its arguments to the XML RPC server properly

    @see HollowXMLRPCServer

    """
    test_target_id = 42
    test_token = 5556
    test_port = 9699

    def setUp(self):
        ClientTestBase.setUp(self)
        self.kclient = KRPC_Responder_Client("")

    def test_ping_arguments(self):
        args = (self.test_address,)
        self._check_args(args, self.kclient.ping)

    def test_find_node_arguments(self):
        args = (self.test_address, self.test_target_id)
        self._check_args(args, self.kclient.find_node)

    def test_get_peers_arguments(self):
        args = (self.test_address, self.test_target_id)
        self._check_args(args, self.kclient.get_peers)

    def test_announce_peer_arguments(self):
        args = (self.test_address,
                self.test_target_id, self.test_token, self.test_port)
        self._check_args(args, self.kclient.announce_peer)

class KRPC_Iterator_Client_TestCase(ClientTestBase, unittest.TestCase):
    """
    These cases test for whether the XML RPC client passes
    its arguments to the XML RPC server properly

    @see HollowXMLRPCServer

    """

    # Use 20 nodes to test as input
    # arguments to the XML RPC client
    test_nodes = [Node(num, ("127.0.0.%d" % num, num)) for num in xrange(2, 22)]
    test_target_id = 55

    def setUp(self):
        ClientTestBase.setUp(self)
        self.kclient = KRPC_Iterator_Client("")

    def test_find_iterate_arguments(self):
        self._test_iterate_funcs_args(self.kclient.find_iterate)

    def test_get_iterate_arguments(self):
        self._test_iterate_funcs_args(self.kclient.get_iterate)

    def _test_iterate_funcs_args(self, func):
        args = (self.test_target_id,)
        self._check_args(args, func)

    def test_find_iterate_argumentsWithNodes(self):
        self._test_iterate_funcs_argsWithNodes(self.kclient.find_iterate)
    
    def test_get_iterate_argumentsWithNodes(self):
        self._test_iterate_funcs_argsWithNodes(self.kclient.get_iterate)

    def _test_iterate_funcs_argsWithNodes(self, func):
        args = (self.test_target_id, self.test_nodes)
        self._check_args(args, func)
