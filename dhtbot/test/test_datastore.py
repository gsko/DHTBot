from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from dhtbot import datastore, constants

class clock(object):
    def __init__(self):
        self._time = 0

    def set(self, time):
        self._time = time

    def time(self):
        return self._time

class HollowReactor(object):
    def __init__(self):
        self.seconds = 0

    def callLater(self, seconds, *args, **kwargs):
        self.seconds = seconds

class DataStoreTestCaseBase(object):
    # Please ensure that you set the
    # self.datastore attribute when subclassing
    # this test class
    def setUp(self):
        self.reactor = HollowReactor()
        self.peer_generator = lambda num: ("127.0.0.1", num)

    def test_empty_get(self):
        m = self.datastore(self.reactor)
        addresses = m.get(50)
        self.assertEqual(0, len(addresses))

    def test_put_and_get_onePeer(self):
        m = self.datastore(self.reactor)
        infohash = 7
        peer = ("1.2.3.4", 8080)
        m.put(infohash, peer)
        addresses = m.get(infohash)
        self.assertEqual(1, len(addresses))
        self.assertEqual(peer, addresses[0])

    def test_put_and_get_tenPeersAcrossMultipleInfohashes(self):
        m = self.datastore(self.reactor)
        # 1 through 10
        infohashes = range(1, 11)
        peers = map(self.peer_generator, infohashes)
        for infohash, peer in zip(infohashes, peers):
            m.put(infohash, peer)
        for infohash in infohashes:
            addresses = list(m.get(infohash))
            self.assertEquals(1, len(addresses))
            self.assertEquals(self.peer_generator(infohash), addresses[0])

    def test_put_verifyProperRemoveTimeout(self):
        self.reactor.seconds = 0
        m = self.datastore(self.reactor)
        infohash = 15
        peer = ("127.0.0.1", 5050)
        m.put(infohash, peer)
        self.assertEqual(constants.peer_timeout, self.reactor.seconds)

    def test_put_verifyProperRemoval(self):
        # Replace the time function of the datastore module
        # so that we can artificially speed up time
        monkey_patcher = MonkeyPatcher()
        c = clock()
        c.set(0)
        monkey_patcher.addPatch(datastore, "time", c)
        # Replace the peer_timeout to 5 seconds
        monkey_patcher.addPatch(constants, "peer_timeout", 5)
        monkey_patcher.patch()
        # Insert a node and verify it is within the datastore
        m = self.datastore(self.reactor)
        infohash = 5
        expected_peer = ("127.0.0.1", 5151)
        m.put(infohash, expected_peer)
        peers = m.get(infohash)
        # Iterate over a 1 element list
        for peer in peers:
            self.assertEqual(expected_peer, peer)
        self.assertEquals(1, len(peers))
        # Change the time and verify that the cleaning function
        # actually removes the peer
        c.set(5)
        # TODO hackish, shouldnt reach into object
        m._cleanup(infohash, peer)
        peers = m.get(infohash)
        self.assertEqual(0, len(peers))
        monkey_patcher.restore()

    def test_put_reannounceResetsTimer(self):
        # Replace the time function of the datastore module
        # so that we can artificially speed up time
        monkey_patcher = MonkeyPatcher()
        c = clock()
        c.set(0)
        monkey_patcher.addPatch(datastore, "time", c)
        # Replace the peer_timeout to 5 seconds
        monkey_patcher.addPatch(constants, "peer_timeout", 5)
        monkey_patcher.patch()
        # Insert a node and verify it is within the datastore
        m = self.datastore(self.reactor)
        infohash = 5
        expected_peer = ("127.0.0.1", 5151)
        m.put(infohash, expected_peer)
        peers = m.get(infohash)
        # Iterate over a 1 element list
        self.assertEquals(1, len(peers))
        for peer in peers:
            self.assertEqual(expected_peer, peer)
        # Change the time and reannounce the peer
        # (make sure the cleanup function doesnt
        #  remove the peer yet)
        c.set(4)
        m.put(infohash, expected_peer)
        peers = m.get(infohash)
        self.assertEqual(1, len(peers))
        m._cleanup(infohash, expected_peer)
        c.set(8)
        m._cleanup(infohash, expected_peer)
        peers = m.get(infohash)
        self.assertEqual(1, len(peers))
        c.set(9)
        m._cleanup(infohash, expected_peer)
        peers = m.get(infohash)
        self.assertEqual(0, len(peers))
        monkey_patcher.restore()

class MemoryDataStoreTestCase(DataStoreTestCaseBase, unittest.TestCase):
    def setUp(self):
        self.datastore = datastore.MemoryDataStore
        DataStoreTestCaseBase.setUp(self)
