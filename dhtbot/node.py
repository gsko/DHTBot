"""
A Twisted TAC file that deploys a daeomonized instance of a DHT Node

"""
from twisted.application import internet, service
from twisted.web import server

from dhtbot.protocols.krpc_responder import KRPC_Responder
from dhtbot.xml_rpc.server_service import KRPC_Responder_Server

udp_port = 1800
node_id = 317981748868523100801836251505537304032928861248L

# Set up the root application
application = service.Application("DHT Daemon")

# The protocol that will drive the heart of this
# application
node_proto = KRPC_Responder(node_id=rand_id)

# Set up the XML RPC wrapper
xml_rpc = KRPC_Responder_Server(node_proto)
node_xml_rpc = service.MultiService()
xml_rpc_tcp = internet.TCPServer(8888, server.Site(xml_rpc))
xml_rpc_tcp.setServiceParent(node_xml_rpc)
node_xml_rpc.setServiceParent(application)

# Set up the actual node that will be receiving, responding to,
# and receiving queries
node_udp = internet.UDPServer(udp_port, node_proto)
node_udp.setServiceParent(node_xml_rpc)
