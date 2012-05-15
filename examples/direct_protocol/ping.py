"""
Standalone example of using the KRPC_Responder protocol

The preferred way to do this in normal Twisted code is by using
twisted services.

"""
from twisted.internet import reactor

from dhtbot.protocols.krpc_responder import KRPC_Responder
from dhtbot.protocols.errors import TimeoutError, KRPCError
from dhtbot import contact

def response_received(ping_response):
    print "Target node has an ID of: %d" % ping_response._queried

def handle_timeout(failure):
    # This code block will only run if the exception was a TimeoutError
    failure.trap(TimeoutError)
    print "Query timed out"

def krpc_error_received(failure):
    # This code block will only run if the exception was a KRPCError
    failure.trap(KRPCError)
    print "Error received: %s" % str(failure.value.error)

def kill_reactor(_ignored):
    # No matter what happens, stop the reactor
    reactor.stop()

proto = KRPC_Responder()

# Function that will run the example
def set_up_query():
    target_address = ("67.18.187.143", 1337)
    # d is a deferred, see the twisted documentation on Deferred's
    d = proto.ping(target_address)
    d.addErrback(handle_timeout)
    d.addErrback(krpc_error_received)
    d.addCallback(response_received)
    d.addBoth(kill_reactor)

# Attach our protocol to a port
reactor.listenUDP(5555, proto)
# Set up our example code once the reactor has started running
reactor.callWhenRunning(set_up_query)
reactor.run()
