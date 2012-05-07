"""
A Twisted TAC file that deploys a daeomonized instance of a DHT Node

"""
from twisted.application import internet, service

from dhtbot.protocols.krpc_responder import KRPC_Responder
from dhtbot.scripts import basic_tester

udp_port = 1800
rand_id = 317981748868523100801836251505537304032928861248L

# Set up the root application
application = service.Application("DHT Daemon")

# Set up the actual node that will be receiving, responding to,
# and receiving queries
node_proto = KRPC_Responder(node_id=rand_id)
node_service = internet.UDPServer(udp_port, node_proto)
node_service.setServiceParent(application)
