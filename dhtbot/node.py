"""
A Twisted TAC file that deploys a daeomonized/rpc'ed instance of a DHT Node

"""
import random

from twisted.application import internet, service
from twisted.web import server

from dhtbot.protocols.krpc_iterator import KRPC_Iterator
from dhtbot.xml_rpc.server_service import KRPC_Iterator_Server

# The udp port on which the DHT node will run
dht_port = 1800
# The tcp port on which the xml_rpc server will run
xml_rpc_port = 8888

# Start with a random node_id on each run
# Note: for better consistency, it is better to choose
# a fixed random ID
#node_id = random.getrandbits(160)
node_id = 317981748868523100801836251505537304032928861248L

# Set up the root application
application = service.Application("DHT Daemon")

# The protocol that will drive the heart of this application
node_proto = KRPC_Iterator(node_id=node_id)

# Set up the XML RPC wrapper
xml_rpc = KRPC_Iterator_Server(node_proto)
node_xml_rpc = service.MultiService()
xml_rpc_tcp = internet.TCPServer(xml_rpc_port, server.Site(xml_rpc))
xml_rpc_tcp.setServiceParent(node_xml_rpc)
node_xml_rpc.setServiceParent(application)

# Set up the actual node that will be receiving, responding to,
# and receiving queries
node_udp = internet.UDPServer(dht_port, node_proto)
node_udp.setServiceParent(node_xml_rpc)
