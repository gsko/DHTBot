"""
@author Greg Skoczek

Implementation of a Quarantine (along with a patcher
that patches this functionality into a KRPC_Responder)
as suggested by section 5B of the subsecond paper

@see references/subsecond.pdf

"""
from twisted.python import log
from twisted.python.components import proxyForInterface

from dhtbot.protocols.errors import TimeoutError, KRPCError
from dhtbot.protocols.krpc_responder import IKRPC_Responder

class Quarantine(object):
    """
    Simulate a quarantine

    A quarantine is an object that will accept a node into
    a temporary 'holding' center where the node will reside until
    it has been verified. A node is verified if it responds to a certain
    number of ping queries within a certain timeout period. Once it has
    been verified, the node is added to the routing table.

    This particular implementation requires that the node respond to atleast
    one ping query (out of a total of two ping queries sent one after another)

    """
    def __init__(self, ping, routing_table):
        self.prison = set()
        self.ping = ping
        self.routing_table = routing_table

    def jail(self, prisoner):
        """
        Introduce the prisoner node into the testing chamber
        
        A prisoner already found in the jail will not be added
        twice. If the prisoner is not in the routing table or
        the prison, it will be tested. If the prisoner
        passes the test, it will be added to the routing table
        
        """
        rt_node = self.routing_table.get_node(prisoner.node_id)
        if rt_node is None and prisoner not in self.prison:
            self.prison.add(prisoner)
            d = self.ping(prisoner.address)
            d.addCallback(lambda ignored_result: prisoner)
            d.addCallback(self.free)
            d.addErrback(self._one_more_chance, prisoner)

    def free(self, prisoner):
        """Transfer the prisoner from the jail to the routing table"""
        if prisoner in self.prison:
            self.prison.remove(prisoner)
            self.routing_table.add_node(prisoner)

    def execute(self, prisoner):
        """Remove the prisoner without adding it to the routing table"""
        if prisoner in self.prison:
            self.prison.remove(prisoner)

    def _one_more_chance(self, failure, prisoner):
        failure.trap(TimeoutError, KRPCError)
        d = self.ping(prisoner.address)
        # Ignore the regular deferred result
        # and pass the prisoner into the free function instead
        d.addCallback(lambda ignored_result: prisoner)
        d.addCallback(self.free)
        d.addErrback(self._remove_prisoner, prisoner)

    def _remove_prisoner(self, failure, prisoner):
        failure.trap(TimeoutError, KRPCError)
        self.execute(prisoner)


class Quarantine_Patcher(proxyForInterface(IKRPC_Responder)):
    """
    Patches quarantine functionality into a KRPC_Responder instance

    @see DHTBot/references/subsecond.pdf : This paper
        covers the quarantine idea
    
    """
    # TODO
    # quarantiner has not been tested
    # NOTICE: there is an idea in DHTBot/ODO that
    # pertains to an enhancement over the original
    # quarantiner implementation

    def __init__(self, original):
        # TODO verify that 'original' satisfies
        # the IKRPC_Responder interface
        self.original = original
        self._quarantine = Quarantine(self.ping, self.routing_table)

    def queryReceived(self, query, address):
        # Find or create node corresponding to this query
        rt_node = self.routing_table.get_node(query._from)
        querying_node = (rt_node if rt_node is not None
                         else contact.Node(query._from, address))
        # Test the querying_node to see if it responds
        # to a ping query, if it does, add it to the routing table
        # @see dhtbot.quarantine.Quarantine.jail
        self._quarantine.jail(querying_node)
        # Relay the query onto the original implementation
        # so that it can dispatch it to the proper "RPCTYPE_Received" method
        return self.original.queryReceived(query, address)
