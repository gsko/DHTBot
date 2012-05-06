"""
@author Greg Skoczek

Module containing various implementations of DataStore's
used for maintaing infohash->peer information

"""
import time
from collections import defaultdict

from dhtbot import constants

class DataStore(object):
    """
    Data storage mechanism for handling DHT put/get requests

    This datastore allows a user to record and retrieve peer info associated
    with a particular infohash in the network

    The datastore is also responsible for removing all peers that
    have not been updated since constants.peer_timeout seconds ago

    """
    def put(self, infohash, address):
        """
        Associate a peer to a particular resource in the network

        The peer associated with 'address' will be recorded as
        having the particular resource associated with 'infohash'
        
        """
        raise NotImplemented

    def get(self, infohash):
        """
        Returns all the peers associated with the given infohash
        
        @return an iterable containing the peers

        """
        raise NotImplemented

class MemoryDataStore(DataStore):
    """
    A DataStore that stores its data in memory

    torrents[] maps an infohash to a dictionary of addresses
    torrents[infohash][] maps an address to its last announce time

    The MemoryDataStore uses the twisted reactor to timeout
    peers that have been announced in the past. Thus the reactor
    must be passed in during the creation of a MemoryDataStore

    """
    def __init__(self, reactor):
        self.reactor = reactor
        self.torrents = defaultdict(dict)

    def put(self, infohash, address):
        """@see Datastore.put"""
        last_announced = time.time()
        self.torrents[infohash][address] = last_announced
        self._register_for_cleanup(infohash, address)

    def get(self, infohash):
        """@see Datastore.get"""
        if infohash in self.torrents:
            return self.torrents[infohash].keys()
        else:
            return list()

    def _register_for_cleanup(self, infohash, address):
        """
        Set up a delayed call that will clean up the peer at the right time

        Specifically, the peer associated with 'infohash' and 'address' will
        be removed after constants.peer_timeout time unless it
        has been updated in between the time this function was called
        and the timeout

        """
        self.reactor.callLater(constants.peer_timeout,
                                self._cleanup, infohash, address)

    def _cleanup(self, infohash, address):
        """
        Remove the peer associated with `infohash` and `address` if timed out

        A peer times out after constants.peer_timeout. However, if a peer
        is re-announced in that interval, the countdown resets

        """
        if (infohash in self.torrents and
                address in self.torrents[infohash]):
            now = time.time()
            age = now - self.torrents[infohash][address]
            if age >= constants.peer_timeout:
                del self.torrents[infohash][address]
                if len(self.torrents[infohash]) == 0:
                    del self.torrents[infohash]
