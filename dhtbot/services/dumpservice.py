# 
# Author: Greg Skoczek
#

import time

from twisted.application import service
from twisted.internet import reactor, task
from twisted.python import log

from dhtbot.coding import krpc_coder, bencode
from dhtbot import constants, contact


class DumpService(service.Service):

    def __init__(self, node_protocol, filename="dhtbot.cache"):
        self.node_protocol = node_protocol
        self.filename = filename

    def startService(self):
        service.Service.startService(self)
        self._load_state()
        self.looping_call = task.LoopingCall(self._dump_state)
        self.looping_call.start(constants.DUMPinterval, now=False)

    def stopService(self):
        service.Service.stopService(self)
        # TODO accessing .running is hackish, is there a proper way?
        if self.looping_call.running:
            self.looping_call.stop()
        self._dump_state()

    def _dump_state(self):
        state_data = dump(self.node_protocol)
        try:
            encoded_state_data = bencode.bencode(state_data)
        except bencode.BTFailure:
            log.msg("Failed to encode state data!")
            return

        with open(self.filename, "w+") as cachefile:
            cachefile.write(encoded_state_data)

    def _load_state(self):
        try:
            encoded_state_data = cachefile.read()
        except IOError:
            log.msg("Couldn't read the cache file")
        except NameError:
            log.msg("Couldn't open the file for reading")
        else:
            try:
                state_data = bencode.bdecode(encoded_state_data)
            except bencode.BTFailure:
                log.msg("Failed to decode state data!")
            finally:
                load(self.node_protocol, state_data)

def dump(node_protocol):
    datadump = dict()

    routing_table_nodes = []
    for kbucket in node_protocol.routing_table.get_kbuckets():
        routing_table_nodes.extend(kbucket.getnodes())
    datadump["rtnodes"] = [dump_node(node) for node in routing_table_nodes]


    datadump["quarantine_nodes"] = [dump_node(node) for
                                            node in node_protocol.quarantine]

    encoded_torrents = dict()
    for infohash, peers in node_protocol.torrents.iteritems():
        encoded_torrents[infohash] = [dump_peer(peer) for peer in peers]
    datadump["torrents"] = encoded_torrents

    datadump["node_id"] = node_protocol.node_id

    return datadump

def load(node_protocol, datadump):
    node_protocol.node_id = datadump["node_id"]

    current_time = time.time()

    for infohash, encoded_peers in datadump["torrents"].iteritems():
        no_timeout_peers = [load_peer(peer) for peer in encoded_peers]
        for peer in no_timeout_peers:
            (address, last_announced) = peer
            age = current_time - last_announced
            if age <= constants.peer_timeout:
                node_protocol._insert_peer(address, infohash, last_announced)

    quarantine_nodes = map(load_node, datadump["quarantine_nodes"])

    rt_nodes = map(load_node, datadump["rtnodes"])
    while len(rt_nodes) > 0:
        node = rt_nodes.pop()
        age = current_time - node.last_updated
        if age <= constants.node_timeout:
            node_protocol.routing_table.addnode(node)
        else:
            quarantine_nodes.add(node)
    
    node_protocol.update_quarantine(quarantine_nodes)

def load_node(list_node):
    [encoded_node, successcount, failcount, totalrtt, last_updated] = list_node
    node = contact.decode_node(encoded_node)
    node.successcount = successcount
    node.failcount = failcount
    node.totalrtt = totalrtt
    node.last_updated = last_updated
    return node

def load_peer(encoded_peer):
    (encoded_address, last_announced) = encoded_peer
    address = contact.decode_address(encoded_address)
    return (address, last_announced)

def dump_node(node):
    dumplist = [contact.encode_node(node), node.successcount,
                node.failcount, node.totalrtt, node.last_updated]
    return dumplist

def dump_peer(peer):
    (address, peerinfo) = peer
    (last_announced, delayed_call) = peerinfo
    dumplist = [contact.encode_address(address), last_announced]
    return dumplist
