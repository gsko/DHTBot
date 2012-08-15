"""
An XML RPC wrapper around the DHT protocols

@see dhtbot.protocols

"""
from twisted.application import service
from twisted.web import xmlrpc

from dhtbot.xml_rpc.common import inflate, deflate

class KRPC_Responder_Server(xmlrpc.XMLRPC):
    """
    Proxy between the XML RPC Server and the running KRPC_Responder Protocol

    The following methods are available:
        ping
        find_node
        get_peers
        announce_peer
    
    These methods send back a deflated result

    @see dhtbot.protocols.krpc_responder.KRPC_Responder
    @see dhtbot.xml_rpc.common

    """
    # Let xmlrpc process None as an argument
    allowNone = True

    # Adding this attribute prevents exceptions
    # in the xmlrpc code. TODO find out why
    useDateTime = True

    def __init__(self, node_proto):
        self.node_proto = node_proto

    def xmlrpc_ping(self, address, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.ping"""
        packed_args = (address, timeout)
        return self._inflate_call_deflate(
                self.node_proto.ping, packed_args)

    def xmlrpc_find_node(self, address, node_id, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.find_node"""
        packed_args = (address, node_id, timeout)
        return self._inflate_call_deflate(
                self.node_proto.find_node, packed_args)

    def xmlrpc_get_peers(self, address, target_id, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.get_peers"""
        packed_args = (address, target_id, timeout)
        return self._inflate_call_deflate(
                self.node_proto.get_peers, packed_args)

    def xmlrpc_announce_peer(self, address, target_id, token, port, timeout):
        """@see dhtbot.protocols.krpc_responder.KRPC_Responder.announce_peer"""
        packed_args = (address, target_id, token, port, timeout)
        return self._inflate_call_deflate(
                self.node_proto.announce_peer, packed_args)

    def _inflate_call_deflate(self, func, args):
        """Inflate the arguments, call the function, deflate its result"""
        inflated_args = (inflate(arg) for arg in args)
        d = func(*inflated_args)
        d.addBoth(deflate)
        return d


class KRPC_Iterator_Server(KRPC_Responder_Server):
    """
    Proxy between the XML RPC Server and the running KRPC_Iterator

    The following methods are available:
        (all of the methods of KRPC_Responder)
        find_iterate
        get_iterate

    These methods send back a deflated result

    @see dhtbot.protocols.krpc_iterator.KRPC_Iterator
    @see dhtbot.xml_rpc.common

    """
    def xmlrpc_find_iterate(self, target_id, nodes, timeout):
        return self._iterate_funcs(self.node_proto.find_iterate,
                target_id, nodes, timeout)

    def xmlrpc_get_iterate(self, target_id, nodes, timeout):
        return self._iterate_funcs(self.node_proto.get_iterate,
                target_id, nodes, timeout)

    def _iterate_funcs(self, func, target_id, nodes, timeout):
        packed_args = (target_id, nodes, timeout)
        return self._inflate_call_deflate(func, packed_args)
