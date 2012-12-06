"""
A Twisted TAC file that deploys a daeomonized/rpc'ed instance of a DHT Node

"""
import random

from twisted.application import internet, service
from twisted.web import server

from dhtbot.protocols.krpc_iterator import KRPC_Iterator
from dhtbot.xml_rpc.server_service import KRPC_Iterator_Server
from dhtbot.constants import dht_port, id_size

# Start with a random node_id on each run
# Note: for better consistency, it is better to choose
# a fixed random ID
node_id = random.getrandbits(id_size)

# Set up the root application
application = service.Application("DHT Daemon")

# The protocol that will drive the heart of this application
dht_proto = KRPC_Iterator(node_id=node_id)

# Set up the actual node that will be receiving, responding to,
# and receiving queries
node_udp = internet.UDPServer(dht_port, dht_proto)
node_udp.setServiceParent(application)
