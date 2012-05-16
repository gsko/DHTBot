from twisted.trial import unittest
from twisted.internet import defer

from dhtbot.contact import Node
from dhtbot.kademlia.routing_table import TreeRoutingTable
from dhtbot.protocols.krpc_iterator import KRPC_Iterator

make_node = lambda num: Node(num, ("127.0.0.1", num))

# Make 65535 nodes for testing
test_nodes = [make_node(num) for num in range(1, 2**16)]

class HollowKRPC_Responder(object):
    """
    Hollowed out KRPC_Responder for testing KRPC_Iterator
    """
    def __init__(self):
        self.node_id = 999
        self.routing_table = TreeRoutingTable(self.node_id)
        self.find_node_count = 0
        self.get_peers_count = 0
        self.defer_gen = defer.Deferred

    def find_node(self, address, node_id, timeout=None):
        self.find_node_count += 1
        return defer_gen()

    def get_peers(self, address, infohash, timeout=None):
        self.get_peers_count += 1
        return defer_gen()

class KRPC_Iterator_TestCase(unittest.TestCase):
    def test_find_iterate_properNumberOfQueries_noNodesInRoutingTable(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_get_iterate_properNumberOfQueries_noNodesInRoutingTable(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_find_iterate_firesAfterAllQueriesFire(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_get_iterate_firesAfterAllQueriesFire(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_find_iterate_getsNodesFromRoutingTable(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_get_iterate_getsNodesFromRoutingTable(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_find_iterate_noNodesRaisesIterationError(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_get_iterate_noNodesRaisesIterationError(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_find_iterate_allQueriesTimeoutRaisesIterationError(self):
        raise unittest.SkipTest("functionality not implemented yet")

    def test_get_iterate_allQueriesTimeoutRaisesIterationError(self):
        raise unittest.SkipTest("functionality not implemented yet")
