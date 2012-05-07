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

    """
    def __init__(self, url):
        """
        Open up the XML RPC Connection so that we can make query calls
        """
        self.server = xmlrpclib.Server(url)

    def sendQuery(self, query, address, timeout):
        """
        Call sendQuery on the remote protocol

        @see dhtbot.protocols.krpc_sender.KRPC_Sender

        """
        # Pickle requires a file, so we simulate one with StringIO
        pickled_output = StringIO.StringIO()
        pickle.dump(query, pickled_output)
        pickled_query = pickled_output.getvalue()
        # Only query needs to be pickled
        # since XML RPC can handle the address (tuple)
        # and timeout (integer)
        pickled_result = self.server.sendQuery(pickled_query, address, timeout)
        result = pickle.load(StringIO.StringIO(pickled_result))
        # Result can be a Response, or one of several exceptions
        # @see dhtbot.protocols.krpc_sender.KRPC_Sender.sendQuery
        return result

class KRPC_Responder_Client(KRPC_Sender_Client):
    def ping(self, address, timeout=constants.rpctimeout):
        pass

    def find_node(self, address, node_id, timeout=constants.rpctimeout):
        pass

    def get_peers(self, address, target_id, timeout=constants.rpctimeout):
        pass

    def announce_peer(self, address, token, port, timeout=constants.rpctimeout):
        pass

