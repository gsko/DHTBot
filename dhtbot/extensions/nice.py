from twisted.python.components import proxyForInterface

from dhtbot.protocols.krpc_responder import IKRPC_Responder

class NICE_Patcher(proxyForInterface(IKRPC_Responder)):
    pass
