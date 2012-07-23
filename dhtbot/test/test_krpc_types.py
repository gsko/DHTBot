from twisted.trial import unittest

from dhtbot.krpc_types import _KRPC, Query, Response, Error

class KRPCTestCase(unittest.TestCase):
    def test_build_repr_empty(self):
        k = _KRPC()
        self.assertEquals("", k._build_repr([]))

    def test_build_repr_setTransactionID(self):
        k = _KRPC()
        k._transaction_id = 109825
        self.assertEquals("_transaction_id=109825",
                            k._build_repr(["_transaction_id"]))

class QueryTestCase(unittest.TestCase):
    def setUp(self):
        self.q = Query()
        self.q._transaction_id = 500
        self.q._from = 27
        self.q.rpctype = "ping"

    def test_build_response(self):
        nodes = []
        token = 8192
        peers = [" "]
        r = self.q.build_response(nodes, token, peers)
        self.assertEquals(self.q._transaction_id, r._transaction_id)
        self.assertEquals(self.q.rpctype, r.rpctype)
        self.assertEquals(nodes, r.nodes)
        self.assertEquals(token, r.token)
        self.assertEquals(peers, r.peers)

    def test_build_error(self):
        code = 203
        message = "Oops, error"
        e = self.q.build_error(code, message)
        self.assertEquals(self.q._transaction_id, e._transaction_id)
        self.assertEquals(code, e.code)
        self.assertEquals(message, e.message)

    def test_repr(self):
        expected_repr = "<Query: _transaction_id=500 rpctype=ping _from=27>"
        self.assertEquals(expected_repr, repr(self.q))

class ResponseTestCase(unittest.TestCase):
    def test_repr(self):
        r = Response()
        r._transaction_id = 18095
        r.queried = 15
        r.token = 1980
        expected_repr = "<Response: _transaction_id=18095 token=1980>"
        self.assertEquals(expected_repr, str(r))

class ErrorTestCase(unittest.TestCase):
    def test_repr(self):
        e = Error()
        e._transaction_id = 222
        e.code = 202
        e.message = "Invalid Query"
        expected_repr = ("<Error: _transaction_id=222 " +
                         "code=202 message='Invalid Query'>")
        self.assertEquals(expected_repr, repr(e))
