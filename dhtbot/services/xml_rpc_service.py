"""
An XML RPC wrapper around the DHT protocols

@see dhtbot.protocols

"""
from twisted.application import service

from dhtbot.protocols.krpc_sender import IKRPC_Sender
from dhtbot.protocols.krpc_responder import IKRPC_Responder

class KRPC_Sender_Server(service.Service):

    implements(IKRPC_Sender)


class KRPC_Responder_Server(service.Service):

    implements(IKRPC_Responder)


