#
# Author: Greg Skoczek
#

import random

from twisted.internet import defer, reactor
from twisted.python import log

from dhtbot.token_cacher import TokenCacher
from dhtbot.protocols.errors import TimeoutError, KRPCError
from dhtbot.protocols.krpc_sender import KRPC_Sender
from dhtbot import constants, contact, krpc_types

class QueryTimeout(Exception):
    pass

class SimpleNodeProtocol(KRPC_Sender):

    def __init__(self, _node_id=None):
        KRPC_Sender.__init__(self, node_id=_node_id)
        self.tokencache = TokenCacher()

    def startProtocol(self):
        KRPC_Sender.startProtocol(self)
        self.bootstrap()

    def _silence_error(self, failure):
            f = failure.trap(TimeoutError, KRPCError)
            if f == KRPCError:
                log.msg("We caused a KRPC Error message to be sent")
            elif f == TimeoutError:
                log.msg("Query timed out!")

    def bootstrap(self):

        def _bootstrap(ip, port, size=10):
            address = (ip, port)
            for i in range(size):
                random_infohash = random.getrandbits(constants.id_size)
                d = KRPC_Sender.find_node(self, address, random_infohash)
                d.addErrback(self._silence_error)

        for node in constants.bootstrap_nodes:
            hostname, port = node
            d = reactor.resolve(hostname)
            d.addCallback(_bootstrap, port, size=4)

    def get_peers(self, address, infohash, timeout=constants.rpctimeout):
        d = KRPC_Sender.get_peers(self, address, infohash)

        def _cache_token(result, tokencache):
            (query, response, responsenode, address) = result
            tokencache.cache(query, response, address)
            return result
        d.addCallback(_cache_token, self.tokencache)
        return d

    def iterate(self, target_id, rpcmethod, timeout):

        # We get: result = (query, response, responsenode, address)
        # We (callback) return: result = (nodes, values, [deferred])
        def _iterator(result, infohash, carrier,
                      rpcmethod, seen_nodes, seen_peers):
                [deferred] = carrier
                if not deferred:
                    return

                query, response, responsenode, address = result
                new_nodes = new_peers = None
                if response.nodes:
                    new_nodes = seen_nodes.symmetric_difference(response.nodes)
                    seen_nodes.update(new_nodes)
                if response.peers:
                    new_peers = seen_peers.symmetric_difference(response.peers)
                    seen_peers.update(new_peers)

                if new_nodes:
                    for node in new_nodes:
                        d = rpcmethod(node.address, target_id)
                        d.addCallback(_iterator, infohash, carrier,
                                      rpcmethod, seen_nodes, seen_peers)
                        d.addErrback(self._silence_error)

                d = defer.Deferred()
                carrier[0] = d
                result = (new_nodes, new_peers, carrier)
                deferred.callback(result)

        def _query_timeout(carrier):
            [deferred] = carrier
            if deferred:
                carrier[0] = None
                deferred.errback(QueryTimeout())

        closestnodes = self.routing_table.get_closest_nodes(target_id)
        seed_response = krpc_types.Response()
        seed_response.nodes = closestnodes
        seed_result = (None, seed_response, None, None)
        carrier = [defer.Deferred()]
        _iterator(seed_result, target_id, carrier, rpcmethod, set(), set())
        reactor.callLater(timeout, _query_timeout, carrier)
        return carrier[0]

    def iterative_get_peers(self, infohash, timeout=constants.query_timeout):
        # TODO is there a way to prettily refactor this?
        d = self.iterate(infohash, self.get_peers, timeout)
        def _sieve(result):
            (nodes, values, carrier) = result
            [deferred] = carrier
            if deferred:
                deferred.addCallback(_sieve)
            return (values, carrier)
        d.addCallback(_sieve)
        return d

    def iterative_find_node(self, node_id, timeout=constants.query_timeout):
        d = self.iterate(node_id, self.find_node, timeout)
        def _sieve(result):
            (nodes, values, carrier) = result
            [deferred] = carrier
            if deferred:
                deferred.addCallback(_sieve)
            return (nodes, carrier)
        d.addCallback(_sieve)
        return d
