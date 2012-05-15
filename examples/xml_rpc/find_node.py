from dhtbot.xml_rpc.client import KRPC_Responder_Client

k = KRPC_Responder_Client("http://localhost:8888")
host = ("67.18.187.143", 1337)
infohash = 0x56CB72C464912215CB5BC1ADEB77E5A50856D887

response = k.find_node(host, infohash)
nodes = response.nodes

for node in nodes:
    print node.node_id, node.address
