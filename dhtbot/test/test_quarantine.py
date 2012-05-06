from twisted.internet.defer import Deferred
from twisted.trial import unittest

from dhtbot.quarantine import Quarantine
from dhtbot.contact import Node
from dhtbot.protocols.errors import TimeoutError

# Helper class for QuarantineTestCase
class HollowRoutingTable(object):
    def __init__(self):
        self.nodes = set()

    def get_node(self, node_id):
        return None

    def add_node(self, node):
        self.nodes.add(node)
        return True

# Helper class for QuarantineTestCase
class PingCounter(object):
    def __init__(self):
        self.ping_count = 0
        self.current_deferred = None

    def ping(self, address):
        self.ping_count += 1
        self.current_deferred = Deferred()
        return self.current_deferred

class QuarantineTestCase(unittest.TestCase):
    def setUp(self):
        self.refresh()

    def refresh(self):
        self.pc = PingCounter()
        self.rt = HollowRoutingTable()

    def test_jail_singlePrisoner(self):
        self.refresh()
        q = Quarantine(self.pc.ping, self.rt)
        n = Node(2**150, ("127.0.0.1", 58))
        q.jail(n)
        self.assertEquals(1, self.pc.ping_count)

    def test_jail_singlePrisonerCallBack(self):
        self.refresh()
        q = Quarantine(self.pc.ping, self.rt)
        n = Node(2**30, ("127.0.0.1", 555))
        q.jail(n)
        # The node should be inserted into the routing
        # table after it 'responds' to a query
        self.assertFalse(n in self.rt.nodes)
        self.assertTrue(n in q.prison)
        self.pc.current_deferred.callback(None)
        self.assertTrue(n in self.rt.nodes)
        self.assertFalse(n in q.prison)

    def test_jail_singlePrisonerErrback(self):
        self.refresh()
        q = Quarantine(self.pc.ping, self.rt)
        n = Node(2**35, ("127.0.0.1", 255))
        q.jail(n)
        self.assertFalse(n in self.rt.nodes)
        self.assertTrue(n in q.prison)
        self.pc.current_deferred.errback(TimeoutError(""))
        self.assertTrue(n in q.prison)
        self.assertFalse(n in self.rt.nodes)

    def test_jail_singlePrisonerErrbackThenCallback(self):
        self.refresh()
        q = Quarantine(self.pc.ping, self.rt)
        n = Node(2**51, ("127.0.0.1", 9555))
        q.jail(n)
        self.assertFalse(n in self.rt.nodes)
        self.assertTrue(n in q.prison)
        self.pc.current_deferred.errback(TimeoutError(""))
        # After the errback, the quarantine should try to
        # ping the node one last time
        self.assertFalse(n in self.rt.nodes)
        self.assertTrue(n in q.prison)
        self.pc.current_deferred.callback("")
        self.assertTrue(n in self.rt.nodes)
        self.assertFalse(n in q.prison)

    def test_jail_singlePrisonerErrbackTwice(self):
        self.refresh()
        q = Quarantine(self.pc.ping, self.rt)
        n = Node(2**35, ("127.0.0.1", 255))
        q.jail(n)
        self.assertFalse(n in self.rt.nodes)
        self.assertTrue(n in q.prison)
        self.pc.current_deferred.errback(TimeoutError(""))
        self.assertFalse(n in self.rt.nodes)
        self.assertTrue(n in q.prison)
        self.pc.current_deferred.errback(TimeoutError(""))
        self.assertFalse(n in q.prison)
        self.assertFalse(n in self.rt.nodes)
