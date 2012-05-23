from twisted.trial import unittest
from twisted.internet import defer

from dhtbot.contact import Node
from dhtbot.kademlia.routing_table import TreeRoutingTable
from dhtbot.protocols.krpc_iterator import KRPC_Iterator
from dhtbot.krpc_types import Response
from dhtbot.protocols.errors import TimeoutError

from dhtbot.test.utils import Counter

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

class DeferredGrabber(object):
    """
    Wrap over sendQuery, recording its arguments/results in a dictionary

    The dictionary is keyed by the transaciton id
    of the given Query
    """
    def __init__(self, sendQuery):
        self.sendQuery = sendQuery
        self.deferreds = dict()
    
    def __call__(self, query, address, timeout=None):
        deferred = self.sendQuery(query, address, timeout)
        # Store the original query and the resulting deferred
        self.deferreds[query.transaction_id] = (query, deferred)

class KRPC_Iterator_TestCase(unittest.TestCase):
    def setUp(self):
        self.k_iter = KRPC_Iterator()
        self.target_id = 5

    # Auxilary test functions
    # that are generalizations of the test
    # cases below
    def _check_k_iter_sendsProperNumberOfQueries_noNodesInRT(self, iter_func):
        self.k_iter.sendQuery = Counter()
        expected_num_queries = 15
        iter_func(self.target_id, test_nodes[:expected_num_queries])
        self.assertEquals(expected_num_queries, self.k_iter.sendQuery.count)

    def _check_k_iter_firesAfterAllQueriesFire(self, iter_func):
        """
        Ensure one 'iterative' query fires after all its subqueries fire
        """
        sendQuery = self.k_iter.sendQuery
        self.k_iter.sendQuery = DeferredGrabber(sendQuery)
        num_queries = 5
        d = iter_func(self.target_id, test_nodes[:num_queries])
        deferreds = self.k_iter.sendQuery.deferreds
        for (query, deferred) in deferreds.items():
            # Grab any node as a response node
            nodes = [test_nodes[55]]
            # Make a valid response node to feed
            # into the subdeferreds
            response = query.build_response(nodes=nodes)
            response._queried = query._querier
            if query.rpctype == "get_peers":
                response.token = 555
            deferred.callback(response)
        # After "receiving a response" to every outgoing
        # query, our main deferred should fire
        self.assertTrue(d.called)

    def _check_k_iter_usesNodesFromRoutingTable(self, iter_func):
        self.k_iter.routing_table.get_closest_nodes = Counter()
        # If we dont supply any testing nodes,
        # the protocol should check its routingtable
        iter_func(self.target_id)
        looked_for_nodes = \
                self.k_iter.routing_table.get_closest_nodes.count > 0
        self.assertTrue(looked_for_nodes)

    def _check_k_iter_raisesIterationErrorOnNoSeedNodes(self, iter_func):
        d = iter_func(self.target_id)
        d.addCallbacks(callback=self._ensure_iteration_error_callback,
                errback=self._ensure_iteration_error_errback)

    def _ensure_iteration_error_errback(self, failure):
        isnt_iteration_error = failure.check(IterationError) is None
        if isnt_iteration_error:
            self.fail("KRPC_Iterator threw an error that wasn't " +
                    "an IterationError")

    def _ensure_iteration_error_callback(self, _ignored_result):
        self.fail("KRPC_Iterator did not throw an IterationError " +
                "and was successful instead")

    def _check_k_iter_failsWhenAllQueriesTimeOut(self, iter_func):
        sendQuery = self.k_iter.sendQuery
        self.k_iter.sendQuery = DeferredGrabber(sendQuery)
        num_queries = 5
        d = iter_func(self.target_id, test_nodes[:num_queries])
        deferreds = self.k_iter.sendQuery.deferreds
        for (query, deferred) in deferreds.items():
            deferred.errback(TimeoutError())
        # Make sure an IterationError was thrown
        d.addCallbacks(callback=self._ensure_iteration_error_callback,
                errback=self._ensure_iteration_error_errback)


    #
    # Find iterate test cases 
    #
    def test_find_iterate_properNumberOfQueriesSent_noNodesInRT(self):
        self._check_k_iter_sendsProperNumberOfQueries_noNodesInRT(
                self.k_iter.find_iterate)

    def test_find_iterate_firesAfterAllQueriesFire(self):
        self._check_k_iter_firesAfterAllQueriesFire(
                self.k_iter.find_iterate)

    def test_find_iterate_usesNodesFromRoutingTable(self):
        self._check_k_iter_usesNodesFromRoutingTable(
                self.k_iter.find_iterate)

    def test_find_iterate_noNodesRaisesIterationError(self):
        self._check_k_iter_raisesIterationErrorOnNoSeedNodes(
                self.k_iter.find_iterate)

    def test_find_iterate_allQueriesTimeoutRaisesIterationError(self):
        self._check_k_iter_failsWhenAllQueriesTimeOut(
                self.k_iter.find_iterate)

    #
    # Get iterate test cases
    #
    def test_get_iterate_properNumberOfQueriesSent_noNodesInRT(self):
        self._check_k_iter_sendsProperNumberOfQueries_noNodesInRT(
                self.k_iter.get_iterate)

    def test_get_iterate_firesAfterAllQueriesFire(self):
        self._check_k_iter_firesAfterAllQueriesFire(
                self.k_iter.get_iterate)

    def test_get_iterate_usesNodesFromRoutingTable(self):
        self._check_k_iter_usesNodesFromRoutingTable(
                self.k_iter.get_iterate)

    def test_get_iterate_noNodesRaisesIterationError(self):
        self._check_k_iter_raisesIterationErrorOnNoSeedNodes(
                self.k_iter.get_iterate)

    def test_get_iterate_allQueriesTimeoutRaisesIterationError(self):
        self._check_k_iter_failsWhenAllQueriesTimeOut(
                self.k_iter.get_iterate)
