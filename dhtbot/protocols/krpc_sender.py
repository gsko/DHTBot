"""
@author Greg Skoczek

This module contains the implementation of a protocol that handles
sending and receiving KRPC Queries, Requests, and Errors. This protocol
is written with the Twisted Network framework

"""
import random
from collections import defaultdict

from zope.interface import implements, Interface
from twisted.python import log
from twisted.internet import reactor, defer, protocol
from twisted.python.components import proxyForInterface
from twisted.internet.interfaces import IUDPTransport

from dhtbot import constants, contact
from dhtbot.kademlia import routing_table
from dhtbot.coding import krpc_coder
from dhtbot.coding.krpc_coder import InvalidKRPCError
from dhtbot.krpc_types import Query, Response, Error
from dhtbot.transaction import Transaction
from dhtbot.protocols.errors import TimeoutError, KRPCError 
from dhtbot.rate_limiter import RateLimiter

class IKRPC_Sender(Interface):
    """
    A protocol that sends and receives KRPC queries, responses, and errors

    See references/kademlia.pdf and references/README for the DHT BEP
    describing these messages in detail. The DHT BEP also specifies
    the behavior required of all nodes in the DHT

    The following attributes are used:
    _reactor: a binding of the reactor that can be passed around
    node_id: the node id of this KRPC_Sender

    @see references/kademlia.pdf
    @see references/bep_0005.html

    """
    def __init__(self, routing_table_class, node_id):
        """
        Construct a KRPC_Sender with a specific routing table and node_id

        @param routing_table_class: class of the routing table to use
        @param node_id: the node_id that this protocol will use
            for operating on the DHT network

        """

    def krpcReceived(self, krpc, address):
        """
        This method is called when a properly decoded krpc needs processing

        If the krpc is a query, it is passed onto queryReceived for further
        processing.
        
        If the krpc is a response or error, an attempt is made to
        find the original query. If it is found, the krpc is passed
        onto either responseReceived or errorReceived (along with
        the transaction). If the original query is not found, the
        orphan krpc is logged

        @param krpc: the krpc message that has been received
        @param address: the origin of this krpc

        """

    def queryReceived(self, query, address):
        """
        This method is called when a krpc query needs processing

        The query is passed onto its corresponding function:
            ping_Received
            find_node_Received
            get_peers_Received
            announce_peer_Received
        for further processing. If these functions cannot be found,
        nothing is done

        """

    def responseReceived(self, response, transaction, address):
        """
        This method is called when a krpc response needs processing

        When a response is received, the corresponding callback
        chain is fired for processing. The callback chain is defined
        in sendQuery

        @see sendQuery

        """

    def errorReceived(self, error, transaction, address):
        """
        This method is called when a krpc error needs processing

        When an error is received, the corresponding errback
        chain is fired for processing. The errback chain is defined
        in sendQuery

        @see sendQuery

        """

    def sendKRPC(self, krpc, address):
        """
        Encode the given krpc and send it to the given address

        If the given krpc is invalid, an exception will be thrown
        in the encoding process

        @raises dhtbot.coding.krpc_coder.InvalidKRPCError

        """

    def sendQuery(self, query, address, timeout):
        """
        Sends the given krpc query to the given address with the given timeout

        @param query: the query that will be encoded and sent
        @param address: the address (ip tuple) that this query will be sent to
        @param timeout: the time after which no responses/errors
                        will be accepted to this query

        @see krpc_types.Response
        @see krpc_types.Error
        @see protocols.errors.KRPCError
        @see protocols.errors.TimeoutError
        @see dhtbot.coding.krpc_coder.InvalidKRPCError

        @returns a deferred whose callback is called with the Response that
            was received, and whose errback is called with a TimeoutError
            when the Query times out, or with a KRPCError when a KRPC Error
            is received in response to the outbound Query, or with an
            InvalidKRPCError when an error was encountered during
            the encoding process

        """

    def sendResponse(self, response, address):
        """
        Send the given krpc response to the given address

        This method does not return a value. However, if an
        error is encountered in the process of encoding the
        given response, an exception will be thrown

        @raises dhtbot.coding.krpc_coder.InvalidKRPCError
        @returns None

        """

    def sendError(self, error, address):
        """
        Send the given krpc response to the given address

        This method does not return a value. However, if an
        error is encountered in the process of encoding the
        given response, an exception will be thrown

        @raises dhtbot.coding.krpc_coder.InvalidKRPCError
        @returns None

        """


class KRPC_Sender(protocol.DatagramProtocol):

    implements(IKRPC_Sender)

    def __init__(self, routing_table_class, node_id):
        self._reactor = reactor
        self.node_id = long(node_id)
        self.transactions = dict()
        self.routing_table = routing_table_class(self.node_id)

    def datagramReceived(self, data, address):
        """
        This method is called by twisted when a datagram is received

        This implementation tries to decode the datagram. If it succeeds,
        it is passed onto self.krpcReceived for further processing, otherwise
        the encoding exception is captured and logged

        @see krpcReceived

        """
        try:
            krpc = krpc_coder.decode(data)
        except InvalidKRPCError:
            log.msg("Malformed packet received from %s:%d" % address)
            return
        self.krpcReceived(krpc, address)

    def krpcReceived(self, krpc, address):
        if isinstance(krpc, Query):
            self.queryReceived(krpc, address)
        else:
            transaction = self.transactions.get(krpc._transaction_id, None)
            if transaction is not None:
                if isinstance(krpc, Response):
                    self.responseReceived(krpc, transaction, address)
                elif isinstance(krpc, Error):
                    self.errorReceived(krpc, transaction, address)
            else:
                log.msg("Received a reply not corresponding to an" +
                        " outstanding query from: %s, reply: %s" % (
                        contact.address_str(address), str(krpc)))

    def queryReceived(self, query, address):
        method_name = "%s_Received" % query.rpctype
        dispatcher = getattr(self, method_name, None)
        if dispatcher is not None:
            dispatcher(query, address)

    def responseReceived(self, response, transaction, address):
        transaction.deferred.callback(response)

    def errorReceived(self, error, transaction, address):
        transaction.deferred.errback(KRPCError(error))

    def sendKRPC(self, krpc, address):
        encoded_packet = krpc_coder.encode(krpc)
        self.transport.write(encoded_packet, address)

    def sendQuery(self, query, address, timeout):
        # Fill in the "from" field of the query
        query._querier = self.node_id
        query._transaction_id = self._generate_transaction_id()
        # Try to send the krpc, there is an encoding error
        # immediately return the error to the user 
        try:
            self.sendKRPC(query, address)
        except InvalidKRPCError as encoding_error:
            return defer.fail(encoding_error)

        # Record this transaction so that later the original
        # query may be referenced when a response/error is received
        t = Transaction()
        t.query = query
        t.address = address
        t.deferred = defer.Deferred()
        # Handle successful responses / errors
        # (supply the address and transaction for extra processing)
        t.deferred.addCallback(self._query_success_callback, address, t)
        t.deferred.addErrback(self._query_failure_errback, address, t)
        # Set up a timeout during which this transaction
        # has to complete (ie: receive a response or error)
        t.timeout_call = self._reactor.callLater(constants.rpctimeout,
                                t.deferred.errback, TimeoutError())
        # Store this transaction
        self.transactions[query._transaction_id] = t
        # Add a callback that removes this transaction
        # after it has been processed
        t.deferred.addBoth(self._remove_transaction_bothback, t)
        return t.deferred

    def sendResponse(self, response, address):
        # Fill out the "from" field on the response before sending
        response._queried = self.node_id
        self.sendKRPC(response, address)

    def sendError(self, error, address):
        self.sendKRPC(error, address)

    def _query_success_callback(self, response, address, transaction):
        """
        Handle a valid Response to an outstanding Query

        This callback records changes to the statistics for the
        node behind the address/response (ie, it updates its RTT
        and makes sures it is in the routing table)

        """
        # Pull the node corresponding to this response out
        # of our routing table, or create it if it doesn't exist
        rt_node = self.routing_table.get_node(response._queried)
        responsenode = (rt_node if rt_node is not None
                        else contact.Node(response._queried, address))
        responsenode.successful_query(transaction.time)
        self.routing_table.offer_node(responsenode)
        # Pass the response further down the callback chain
        return response

    def _query_failure_errback(self, failure, address, transaction):
        """
        Handle exceptions encountered while waiting for a Response

        This errback processes TimeoutErrors and KRPCErrors.
        Specifically, it updates the statistics of the node
        responsible for the exception (if it can be found),
        and removes it from the routing table if necessary

        """
        # Only enter this code block if the error
        # is either a TimeoutError or a KRPCError
        f = failure.trap(TimeoutError, KRPCError)
        errornode = self.routing_table.get_node_by_address(address)
        if errornode is not None:
            if f == TimeoutError:
                # TODO introduce a better determination
                # for whether to remove a node (besides .fresh())
                if not errornode.fresh():
                    self.routing_table.remove_node(errornode)
            elif f == KRPCError:
                errornode.failed_query(transaction.time)
        return failure

    def _remove_transaction_bothback(self, result, transaction):
        """
        Callback/errback that removes an outstanding transaction

        The corresponding timeout delayed call is also cancelled
        if it has not yet been called

        """
        transaction_id = transaction.query._transaction_id
        if transaction_id in self.transactions:
                del self.transactions[transaction_id]
                if transaction.timeout_call.active():
                    transaction.timeout_call.cancel()
        return result

    def _generate_transaction_id(self):
        """
        Generate a transaction_id unique to our transaction table

        @see dhtbot.constants.transaction_id_size
        @returns a unique transaction_id of constants.transaction_id_size size

        """
        while True:
            transaction_id = random.getrandbits(constants.transaction_id_size)
            if transaction_id not in self.transactions:
                return transaction_id


class KRPCRateLimiter(proxyForInterface(IKRPC_Sender, '_original')):
    """
    Limits the rate at which queries can enter/exit this protocol

    The object passed in to the constructor should implement
    IKRPC_Sender. The passed in object will be overridden in
    such a way that only a particular amount of bytes will
    be allowed to be received/sent at a time (on a global
    and per host limit)

    @see dhtbot.rate_limiter.RateLimiter
    @see dhtbot.constants.host_bandwidth_rate
    @see dhtbot.constants.global_bandwidth_rate

    """
    # TODO this method should not be needed, but
    # removing it causes weird errors
    def __init__(self, original):
        self._original = original

    def startProtocol(self):
        self._original.startProtocol()
        self._incoming_rate_limiter = RateLimiter()
        self._outgoing_rate_limiter = RateLimiter()

    def sendKRPC(self, krpc, address):
        encoded_krpc = krpc_coder.encode(krpc)
        enough_bandwidth_to_send = \
                self._outgoing_rate_limiter.consume(encoded_krpc, address)
        if enough_bandwidth_to_send:
            self._original.sendKRPC(krpc, address)

    def datagramReceived(self, datagram, address):
        # Only pass datagrams down the processing chain
        # if the rate limiter agrees
        enough_bandwidth_to_accept = \
                self._incoming_rate_limiter.consume(datagram, address)
        if enough_bandwidth_to_accept:
            self._original.datagramReceived(datagram, address)
