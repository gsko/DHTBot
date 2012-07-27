import pickle
import StringIO

from twisted.web import xmlrpc, server
from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.python.monkey import MonkeyPatcher

from dhtbot import constants, xml_rpc
from dhtbot.contact import Node
from dhtbot.xml_rpc.client import (KRPC_Sender_Client,
        KRPC_Responder_Client, KRPC_Iterator_Client)
from dhtbot.krpc_types import Query

monkey_patcher = MonkeyPatcher()

class HollowXMLRPCServer(object):
    """
    With the exception of sendQuery, all of the public
    functions of this class act as proxy functions that
    simply pass through all of the received arguments.

    This means that this "server" can be used to
    collect all outbound xml rpc client arguments.

    (Hint: monkey patch this class over
    'ServerProxy' attribute of xmlrpclib for the
    dhtbot.xml_rpc.client module and compare the
    outbound arguments to those that you expected)

    This class is used in the KRPC_Responder_Client and
    KRPC_Iterator_Client test cases.

    """
    def __init__(self, url, allow_none=False):
        pass

    def sendQuery(self, pickled_query, address, timeout):
        self.pickled_query = pickled_query
        self.address = address
        self.timeout = timeout
        # We pass back a valid pickled response
        input = StringIO.StringIO(pickled_query)
        query = pickle.load(input)
        response = query.build_response()
        response._from = 11111
        output = StringIO.StringIO()
        pickle.dump(response, output)
        return output.getvalue()
    
    def ping(self, address, timeout=constants.rpctimeout):
        args = [address]
        self._none_check(args, timeout)
        return pickle.dumps(args)

    def find_node(self, address, target_id, timeout=constants.rpctimeout):
        args = [address, target_id]
        self._none_check(args, timeout)
        return pickle.dumps(args)

    def get_peers(self, address, target_id, timeout=constants.rpctimeout):
        args = [address, target_id]
        self._none_check(args, timeout)
        return pickle.dumps(args)

    def announce_peer(self, address, target_id, token,
            port, timeout=constants.rpctimeout):
        args = [address, target_id, token, port]
        self._none_check(args, timeout)
        return pickle.dumps(args)

    def find_iterate(self, target_id, nodes=None, timeout=None):
        args = [target_id]
        self._none_check(args, nodes, timeout)
        return pickle.dumps(args)

    def get_iterate(self, target_id, nodes=None, timeout=None):
        args = [target_id]
        self._none_check(args, nodes, timeout)
        return pickle.dumps(args)

    def _none_check(self, args, *args_to_check):
        """
        Add all non-None arguments to the args list
        since they will be tested for

        """
        for arg in args_to_check:
            if arg is not None:
                args.append(arg)
        

    def _valid_sendQuery_arguments(self, query, address, timeout):
        """
        Verify that the client arguments transmit to the server succesfully

        After checking, this function will erase the recorded arguments
        (so the upcoming calls do not make mistakes)

        @returns Boolean indicating whether the arguments transmitted properly

        """
        output = StringIO.StringIO()
        pickle.dump(query, output)
        pickled_query = output.getvalue()
        is_equal = (pickled_query == self.pickled_query and
                 address == self.address and
                 timeout == self.timeout)
        self.pickled_query = None
        self.address = None
        self.timeout = None
        return is_equal

class ClientTestBase(object):
    """
    Ensure the client passes valid arguments to the server
    """

    test_address = ("127.0.0.1", 58585)
    test_timeout = 15

    def setUp(self):
        monkey_patcher.addPatch(xml_rpc.client.xmlrpclib,
                                "ServerProxy", HollowXMLRPCServer)
        monkey_patcher.patch()
        # Empty string is ok, since we monkey patched
        # over the xmlrpclib.Server
        self.kclient = KRPC_Sender_Client("")

    def tearDown(self):
        monkey_patcher.restore()

class KRPC_Sender_Client_TestCase(ClientTestBase, unittest.TestCase):
    def test_sendQuery_arguments(self):
        query = Query()
        query.rpctype = "ping"
        query._from = 1515
        query._transaction_id = 636363
        _ignored = self.kclient.sendQuery(query,
                            self.test_address, self.test_timeout)
        self.assertTrue(self.kclient.server._valid_sendQuery_arguments(
                        query, self.test_address, self.test_timeout))

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
        args = [self.test_address]
        passed_args = self.kclient.ping(*args)
        self.assertEquals(args, passed_args)

    def test_find_node_arguments(self):
        args = [self.test_address, self.test_target_id]
        passed_args = self.kclient.find_node(*args)
        # convert the target_id into a str
        # since that is how it is sent
        args[1] = str(args[1])
        self.assertEquals(args, passed_args)

    def test_get_peers_arguments(self):
        args = [self.test_address, self.test_target_id]
        passed_args = self.kclient.get_peers(*args)
        # convert the target_id into a str
        # since that is how it is sent
        args[1] = str(args[1])
        self.assertEquals(args, passed_args)

    def test_announce_peer_arguments(self):
        args = [self.test_address,
                self.test_target_id, self.test_token, self.test_port]
        passed_args = self.kclient.announce_peer(*args)
        # convert the target_id into a str
        # since that is how it is sent
        args[1] = str(args[1])
        self.assertEquals(args, passed_args)

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
        self._test_iterate_funcs_args(
                self.kclient.find_iterate)

    def test_get_iterate_arguments(self):
        self._test_iterate_funcs_args(
                self.kclient.get_iterate)

    def _test_iterate_funcs_args(self, func):
        expected_args = [self.test_target_id]
        actual_args = func(*expected_args)
        # convert the target_id into a str
        # since that is how it is sent
        expected_args[0] = str(expected_args[0])
        self.assertEquals(expected_args, actual_args)

    def test_find_iterate_argumentsWithNodes(self):
        self._test_iterate_funcs_argsWithNodes(
                self.kclient.find_iterate)
    
    def test_get_iterate_argumentsWithNodes(self):
        self._test_iterate_funcs_argsWithNodes(
                self.kclient.get_iterate)

    def _test_iterate_funcs_argsWithNodes(self, func):
        expected_args = [self.test_target_id, self.test_nodes]
        actual_args = func(*expected_args)
        # convert the target_id into a str
        # and convert pickle the nodes
        # since that is how they are sent
        expected_args[0] = str(expected_args[0])
        expected_args[1] = pickle.dumps(self.test_nodes)
        self.assertEquals(expected_args, actual_args)
