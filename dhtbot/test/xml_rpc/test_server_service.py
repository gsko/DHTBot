from twisted.trial import unittest


from dhtbot.xml_rpc.server_service import (KRPC_Sender_Server,
        KRPC_Responder_Server, KRPC_Iterator_Server)


class Hollow_KRPC_Iterator(object):
    """
    Simple class that implements all KRPC_Iterator methods
    and dumps all collected arguments with each call

    ie:

    >>> hk = Hollow_KRPC_Iterator()
    >>> hk.find_iterate(42)
    >>> hk.args
    (42, None, None)
    >>> hk.called == hk.find_iterate
    True
    >>> 

    """
    ## KRPC_Sender
    #

    def sendQuery(self, query, address, timeout=None):
        self.args = (query, address, timeout)
        self.called = self.sendQuery

    #
    #

    ## KRPC_Responder
    #

    def ping(self, address, timeout=None):
        self.args = (address, timeout)
        self.called = self.ping

    def find_node(self, address, node_id, timeout=None):
        self.args = (address, node_id, timeout)
        self.called = self.find_node

    def get_peers(self, address, target_id, timeout=None):
        self.args = (address, target_id, timeout)
        self.called = self.get_peers

    def announce_peer(self, address, target_id, token, port, timeout=None):
        self.args = (address, target_id, token, port, timeout)
        self.called = self.announce_peer

    #
    #

    ## KRPC_Iterator
    #

    def find_iterate(self, target_id, nodes=None, timeout=None):
        self.args = (target_id, nodes, timeout)
        self.called = self.find_iterate

    def get_iterate(self, target_id, nodes=None, timeout=None):
        self.args = (target_id, nodes, timeout)
        self.called = self.get_iterate

class KRPC_Sender_Server_TestCase(unittest.TestCase):
    pass
