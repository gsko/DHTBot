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

class KRPC_Sender_Client(object):
    """
    Encode function call arguments and decode their results

    All arguments and results are encoded/decoded, so this class
    can be used as a KRPC_Sender would normally be used.

    Note: only sendQuery has been provided. All other methods
    are not yet accessible via the RPC interface

    @see dhtbot.protocols.krpc_sender.KRPC_Sender

    """
    def __init__(self, url):
        """
        Open up the XML RPC Connection so that we can make query calls
        """
        self.server = xmlrpclib.ServerProxy(url, allow_none=True)

    def sendQuery(self, query, address, timeout):
        """
        Call sendQuery on the remote protocol

        @see dhtbot.protocols.krpc_sender.KRPC_Sender.sendQuery

        """
        pickled_query = pickle.dumps(query)
        # Only query needs to be pickled
        # since XML RPC can handle the address (tuple)
        # and timeout (integer)
        pickled_result = self.server.sendQuery(pickled_query, address, timeout)
        result = pickle.loads(pickled_result)
        # Result can be a Response, or one of several exceptions
        # @see dhtbot.protocols.krpc_sender.KRPC_Sender.sendQuery
        # for more details on return values
        return result

class KRPC_Responder_Client(KRPC_Sender_Client):
    """
    Support ping/find_node/get_peers/announce_peer over rpc

    @see KRPC_Sender_Client

    """
    def ping(self, address, timeout=None):
        pickled_result = self.server.ping(address, timeout)
        return pickle.loads(pickled_result)

    def find_node(self, address, node_id, timeout=None):
        packed_node_id = str(node_id)
        pickled_result = self.server.find_node(
                address, packed_node_id, timeout)
        return pickle.loads(pickled_result)

    def get_peers(self, address, target_id, timeout=None):
        packed_target_id = str(target_id)
        pickled_result = self.server.get_peers(
                address, packed_target_id, timeout)
        return pickle.loads(pickled_result)

    def announce_peer(self, address, target_id, token, port, timeout=None):
        packed_target_id = str(target_id)
        pickled_result = self.server.announce_peer(
                address, packed_target_id,  token, port, timeout)
        return pickle.loads(pickled_result)

class KRPC_Iterator_Client(KRPC_Responder_Client):
    """
    Support find_iterate/get_iterate calls over rpc

    @see KRPC_Iterator_Client

    """
    def find_iterate(self, target_id, nodes=None, timeout=None):
        func = self.server.find_iterate
        return self._encode_and_pass(func, target_id, nodes, timeout)

    def get_iterate(self, target_id, nodes=None, timeout=None):
        func = self.server.get_iterate
        return self._encode_and_pass(func, target_id, nodes, timeout)

    def _encode_and_pass(self, func, target_id, nodes, timeout):
        packed_target_id = str(target_id)
        # if nodes is None, then None will be returned
        # else, the nodes will be encoded
        packed_nodes = nodes and pickle.dumps(nodes)
        pickled_result = func(packed_target_id, packed_nodes, timeout)
        return pickle.loads(pickled_result)
