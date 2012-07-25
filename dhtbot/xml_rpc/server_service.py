"""
An XML RPC wrapper around the DHT protocols

@see dhtbot.protocols

"""
from twisted.application import service
from twisted.web import xmlrpc

from dhtbot.protocols.krpc_sender import IKRPC_Sender
from dhtbot.protocols.krpc_responder import IKRPC_Responder
from dhtbot.xml_rpc.client import unpickle_from_str, pickle_to_str

class KRPC_Sender_Server(xmlrpc.XMLRPC):
    """
    Proxy between the XML RPC Server and the running KRPC_Sender Protocol

    sendQuery is the only proxied function from KRPC_Sender

    @see dhtbot.protocols.krpc_sender.KRPC_Sender

    """

    # Allow this XMLRPC server to transmit None
    allowNone = True
    # useDateTime was enabled because otherwise
    # exceptions were triggered in the XML RPC connection
    # process. (This may be able to be removed)
    # TODO investigate
    useDateTime = True

    def __init__(self, node_proto):
        self.node_proto = node_proto

    def xmlrpc_sendQuery(self, pickled_query, address, timeout):
        """@see dhtbot.protocols.krpc_sender.KRPC_Sender.sendQuery"""
        # xml_rpc encodes tuples into lists, so we reverse the process
        address = tuple(address)
        # The query was pickled so it could be sent over XMLRPC
        query = unpickle_from_str(pickled_query)
        deferred = self.node_proto.sendQuery(query, address, timeout)
        # Pickle the result so that it can be sent over XMLRPC
        deferred.addCallback(pickle_to_str)
        return deferred

class KRPC_Responder_Server(KRPC_Sender_Server):
    """
    Proxy between the XML RPC Server and the running KRPC_Responder Protocol

    The following methods are available:
        sendQuery
        ping
        find_node
        get_peers
        announce_peer
    
    These methods send back a deferred that returns
    a pickled version of the result

    @see dhtbot.protocols.krpc_responder.KRPC_Responder

    """
    def xmlrpc_ping(self, address, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.ping"""
        address = tuple(address)
        d = self.node_proto.ping(address, timeout)
        d.addCallback(pickle_to_str)
        return d

    def xmlrpc_find_node(self, address, packed_node_id, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.find_node"""
        address = tuple(address)
        node_id = long(packed_node_id)
        d = self.node_proto.find_node(address, node_id, timeout)
        d.addCallback(pickle_to_str)
        return d

    def xmlrpc_get_peers(self, address, packed_target_id, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.get_peers"""
        address = tuple(address)
        target_id = long(packed_target_id)
        d = self.node_proto.get_peers(address, target_id, timeout)
        d.addCallback(pickle_to_str)
        return d

    def xmlrpc_announce_peer(self,
            address, packed_target_id, token, port, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.announce_peer"""
        address = tuple(address)
        target_id = long(packed_target_id)
        d = self.node_proto.announce_peer(address, token, port, timeout)
        d.addCallback(pickle_to_str)
        return d

class KRPC_Iterator_Server(KRPC_Responder_Server):
    """
    Proxy between the XML RPC Server and the running KRPC_Iterator

    The following methods are available:
        (all of the methods of KRPC_Responder and KRPC_Sender)
        find_iterate
        get_iterate

    These methods send back a deferred that returns
    a pickle version of the result

    """
    def xmlrpc_find_iterate(self, packed_target_id, pickled_nodes, timeout):
        self._iterate_funcs(self.node_proto.find_iterate,
                packed_target_id, pickled_nodes, timeout)

    def xmlrpc_get_iterate(self, packed_target_id, pickled_nodes, timeout):
        self._iterate_funcs(self.node_proto.get_iterate,
                packed_target_id, pickled_nodes, timeout)

    def _iterate_funcs(self, func, packed_target_id, pickled_nodes, timeout):
        target_id = long(packed_target_id)
        # if pickled_nodes is None, None will be returned
        # else the nodes will be unpickled
        nodes = pickled_nodes and unpickle_from_str(pickled_nodes)
        d = self.node_proto.find_iterate(target_id, nodes, timeout)
        d.addCallback(pickle_to_str)
        return d
