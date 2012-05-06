from twisted.internet import reactor

from dhtbot.protocols.krpc_responder import KRPC_Responder
from dhtbot.protocols.errors import TimeoutError, KRPCError
from dhtbot import contact

def response_received(ping_response):
    print "Target node has an ID of: %d" % ping_response._queried

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
    d = proto.ping(target_address)
    d.addErrback(handle_timeout)
    d.addErrback(krpc_error_received)
    d.addCallback(response_received)
    d.addBoth(kill_reactor)

reactor.listenUDP(5555, proto)
reactor.callWhenRunning(set_up_query)
reactor.run()
