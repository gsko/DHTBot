import pickle
import StringIO

from twisted.web import xmlrpc, server
from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.python.monkey import MonkeyPatcher

from dhtbot import xml_rpc_client
from dhtbot.xml_rpc_client import KRPC_Sender_Client
from dhtbot.krpc_types import Query

monkey_patcher = MonkeyPatcher()

class HollowXMLRPCServer(object):

    def __init__(self, url):
        pass

    def sendQuery(self, pickled_query, address, timeout):
        self.pickled_query = pickled_query
        self.address = address
        self.timeout = timeout
        # We pass back a valid pickled response
        input = StringIO.StringIO(pickled_query)
        query = pickle.load(input)
        response = query.build_response()
        response._queried = 11111
        output = StringIO.StringIO()
        pickle.dump(response, output)
        return output.getvalue()

    def _valid_arguments(self, query, address, timeout):
        """
        Verify that the client arguments transmit to the server succesfully

        After checking, this function will erase the recorded arguments
        (so the upcoming calls do not make mistakes)

        @returns Boolean indicating whether the arguments transmitted properly

        """
        output = StringIO.StringIO()
        pickle.dump(query, output)
        pickled_query = output.getvalue()
        equal = (pickled_query == self.pickled_query and
                 address == self.address and
                 timeout == self.timeout)
        self.pickled_query = None
        self.address = None
        self.timeout = None
        return equal

class KRPC_Sender_Client_TestCase(unittest.TestCase):

    test_address = ("127.0.0.1", 58585)
    test_timeout = 15

    def setUp(self):
        monkey_patcher.addPatch(xml_rpc_client.xmlrpclib,
                                "Server", HollowXMLRPCServer)
        monkey_patcher.patch()

    def tearDown(self):
        monkey_patcher.restore()

    def test_sendQuery_argsTransmitSuccessfully(self):
        """
        Ensure the client passes valid arguments to the server
        """
        # Empty string is ok, since we monkey patched
        # over the xmlrpclib.Server
        kclient = KRPC_Sender_Client("")
        query = Query()
        query.rpctype = "ping"
        query._querier = 1515
        query._transaction_id = 636363
        _ignored = kclient.sendQuery(query,
                            self.test_address, self.test_timeout)
        self.assertTrue(kclient.server._valid_arguments(
                        query, self.test_address, self.test_timeout))
