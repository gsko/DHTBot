"""
@author Greg Skoczek

Module containing an iterative KRPC protocol along with auxilary classes

"""

class IterationError(Exception):
    """
    Error indicating a fault has occured in the KRPC_Iterator

    Possible reasons for this can be:
        * There are no nodes in the routing table and no nodes
            were provided as arguments into the iterator
        * All outbound queries timed out

    The reason can be accessed as a string in the 'reason' attribute

    """
    def __init__(self, reason):
        """
        @param reason: a string describing the interation error
        """
        self.reason = reason

class KRPC_Iterator(object):
    """
    KRPC_Iterator abstracts the practice of iterating toward a target ID

    This iterator uses an instance of a KRPC_Responder to send its
    outgoing queries
    """
    def __init__(self, node_proto):
        """
        @param node_proto: the KRPC_Responder used for sending queries
        """
        self.node_proto = node_proto

    def find_iterate(self, target_id, nodes=None):
        """
        Run a find_node query on every node in a list and return the new nodes

        This function will take the nodes closest to the target_id (from
        either the routing table or the provided nodes argument) and
        send a find_node query to each one. After all queries have either
        returned a response or timed out, all newly found nodes will be
        returned in a deferred callback.

        @param nodes: the nodes to start the iteration from (if no nodes
            are provided, nodes will be taken from the routing table)
        @returns a deferred that fires its callback with a set of all
            newly discovered nodes or fires its errback with an IterationError

        @see IterationError

        """

    def get_iterate(self, target_id, nodes=None):
        """
        Run a get_peers query on every node in a list and return new nodes/peers

        This function will take the nodes closest to the target_id (from
        either the routing table or the provided nodes argument) and
        send a get_peers query to each one. After all queries have either
        returned a response or timed out, all newly found nodes and peers
        will be returned in a deferred callback.

        @param nodes: the nodes to start the iteration from (if no nodes
            are provided, nodes will be taken from the routing table)
        @returns a deferred that fires its callback with a tuple (peers, nodes)
            where
                peers: a set of all newly discovered peers (if any)
                nodes: a set of all newly discovered nodes (if the queried
                    node did not have any peers, it returns nodes instead)
            The errback is fired with an IterationError if an error occurs
            in the iteration process.

        @see IterationError

        """

    def _iterate(self, iterate_func, target_id, nodes=None):
        """
        Perform one iteration towards the target_id

        @param iterate_func: the function used to iterate towards the
            target id. This function is either get_peers or find_node
            as found on KRPC_Responder
        @returns a deferred which fires the callback with a tuple
            (peers, nodes), where
                peers: all the new peers that have been discovered
                    (if the iterate_func is get_peers)
                nodes: all the new nodes that been discovered
            The errback is fired with an IterationError if an
            error occurs in the iteration

        @see IterationError

        """
