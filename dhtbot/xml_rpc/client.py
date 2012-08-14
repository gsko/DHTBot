"""
Simple XML RPC Clients for the corresponding XML RPC Servers

Note: this code uses blocking I/O from pythons built in
xmlrpclib implementation

@see dhtbot.services.xml_rpc_service
    This modules contains the server side code of the XMLRPC

"""
import xmlrpclib
import pickle

from dhtbot import constants

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

    def _pickle_and_feed(self, args, func):
        pickled_args = (pickle.dumps(arg) for arg in args)
        pickled_result = func(*pickled_args)
        return pickle.loads(pickled_result)

    def ping(self, address, timeout=None):
        args = (address, timeout)
        return self._pickle_and_feed(args, self.server.ping)

    def find_node(self, address, node_id, timeout=None):
        args = (address, node_id, timeout)
        return self._pickle_and_feed(args, self.server.find_node)

    def get_peers(self, address, target_id, timeout=None):
        args = (address, target_id, timeout)
        return self._pickle_and_feed(args, self.server.get_peers)

    def announce_peer(self, address, target_id, token, port, timeout=None):
        args = (address, target_id, token, port, timeout)
        return self._pickle_and_feed(args, self.server.announce_peer)

class KRPC_Iterator_Client(KRPC_Responder_Client):
    """
    Support find_iterate/get_iterate calls over rpc

    @see KRPC_Iterator_Client

    """
    def find_iterate(self, target_id, nodes=None, timeout=None):
        args = (target_id, nodes, timeout)
        return self._pickle_and_feed(args, self.server.find_iterate)

    def get_iterate(self, target_id, nodes=None, timeout=None):
        args = (target_id, nodes, timeout)
        return self._pickle_and_feed(args, self.server.get_iterate)
