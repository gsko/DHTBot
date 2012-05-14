from dhtbot.xml_rpc.client import KRPC_Responder_Client

k = KRPC_Responder_Client("http://localhost:8888")
host = ("67.18.187.143", 1337)
print k.ping(host)
