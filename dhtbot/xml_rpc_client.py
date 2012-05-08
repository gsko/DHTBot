"""
Simple XML RPC Clients for the corresponding XML RPC Servers

Note: this code uses blocking I/O from pythons built in
xmlrpclib implementation

@see dhtbot.services.xml_rpc_service
    This modules contains the server side code of the XMLRPC

"""
import xmlrpclib
import StringIO
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
        self.server = xmlrpclib.Server(url)

    def sendQuery(self, query, address, timeout):
        """
        Call sendQuery on the remote protocol

        @see dhtbot.protocols.krpc_sender.KRPC_Sender.sendQuery

        """
        pickled_query = _pickle_dump_string(query)
        # Only query needs to be pickled
        # since XML RPC can handle the address (tuple)
        # and timeout (integer)
        pickled_result = self.server.sendQuery(pickled_query, address, timeout)
        result = _pickle_load_string(pickled_result)
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
        return self.server.ping(address, timeout)

    def find_node(self, address, node_id, timeout=None):
        return self.server.find_node(address, node_id, timeout)

    def get_peers(self, address, target_id, timeout=None):
        return self.server.get_peers(address, target_id, timeout)

    def announce_peer(self, address, token, port, timeout=None):
        return self.server.announce_peer(address, token, port, timeout)

def _pickle_dump_string(obj):
    """
    Pickle an object directly to a string
    """
    # Simulate file IO with the StringIO object
    output_file = StringIO.StringIO()
    pickle.dump(obj, output_file)
    return output_file.getvalue()

def _pickle_load_string(obj_str):
    """
    Unpickle an object directly from a string
    """
    # Simulate file IO with the StringIO object
    input_file = StringIO.StringIO(obj_str)
    obj = pickle.load(input_file)
    return obj
