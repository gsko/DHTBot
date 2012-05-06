from twisted.internet import reactor

from dhtbot.protocols.krpc_responder import KRPC_Responder
from dhtbot.protocols.errors import TimeoutError, KRPCError
from dhtbot import contact

def response_received(response):
    print "Target node has an ID of: %d" % response._queried
    for node in response.nodes:
        print str(node)

def handle_timeout(failure):
    failure.trap(TimeoutError)
    print "Query timed out"

def krpc_error_received(failure):
    failure.trap(KRPCError)
    print "Error received"

def kill_reactor(_ignored):
    reactor.stop()

proto = KRPC_Responder()

def set_up_query():
    target_address = ("67.18.187.143", 1337)
    target_id = long("0x39B8258834EDFB00A4219BCECA7D82A754A3AFC2", 16)
    d = proto.find_node(target_address, target_id)
    d.addErrback(handle_timeout)
    d.addErrback(krpc_error_received)
    d.addCallback(response_received)
    d.addBoth(kill_reactor)

reactor.listenUDP(7555, proto)
reactor.callWhenRunning(set_up_query)
reactor.run()
