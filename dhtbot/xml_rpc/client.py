"""
Simple XML RPC Clients for the corresponding XML RPC Servers

Note: this code uses blocking I/O from pythons built in
xmlrpclib implementation

@see dhtbot.services.xml_rpc_service
    This modules contains the server side code of the XMLRPC

"""
import xmlrpclib

from dhtbot import constants
from dhtbot.xml_rpc.common import inflate, deflate

class KRPC_Responder_Client(object):
    """
    Support ping/find_node/get_peers/announce_peer over rpc

    @see KRPC_Responder_Client

    """

    def __init__(self, url):
        """
        Open up the XML RPC Connection so that we can make query calls
        """
        self.server = xmlrpclib.ServerProxy(url, allow_none=True)

    def ping(self, address, timeout=None):
        args = (address, timeout)
        return self._deflate_call_inflate(args, self.server.ping)

    def find_node(self, address, node_id, timeout=None):
        args = (address, node_id, timeout)
        return self._deflate_call_inflate(args, self.server.find_node)

    def get_peers(self, address, target_id, timeout=None):
        args = (address, target_id, timeout)
        return self._deflate_call_inflate(args, self.server.get_peers)

    def announce_peer(self, address, target_id, token, port, timeout=None):
        args = (address, target_id, token, port, timeout)
        return self._deflate_call_inflate(args, self.server.announce_peer)

    def _deflate_call_inflate(self, args, func):
        deflated_args = (deflate(arg) for arg in args)
        deflated_result = func(*deflated_args)
        return inflate(deflated_result)

class KRPC_Iterator_Client(KRPC_Responder_Client):
    """
    Support find_iterate/get_iterate calls over rpc

    @see KRPC_Iterator_Client

    """
    def find_iterate(self, target_id, nodes=None, timeout=None):
        args = (target_id, nodes, timeout)
        return self._deflate_call_inflate(args, self.server.find_iterate)

    def get_iterate(self, target_id, nodes=None, timeout=None):
        args = (target_id, nodes, timeout)
        return self._deflate_call_inflate(args, self.server.get_iterate)
