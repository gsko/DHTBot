#
# Author: Greg Skoczek

import random

from twisted.application import service
from twisted.internet import task
from twisted.python import log

from dhtbot import constants

class NICEService(service.Service):

    def __init__(self, node_protocol):
        self.node_protocol = node_protocol

    def startService(self):
        service.Service.startService(self)
        self.looping_call = task.LoopingCall(self.NICE)
        self.looping_call.start(constants.NICEinterval)

    def stopService(self):
        service.Service.stopService(self)
        self.looping_call.stop()

    def NICE(self):
        kbuckets = self.node_protocol.routing_table.get_kbuckets()
        kbucket = random.choice(kbuckets)
        nice_node = kbucket.stalest_node()
        if nice_node:
            self.node_protocol.ping(nice_node.address)
