#
# Author: Greg Skoczek
#

from twisted.application import service
from twisted.python import log


class ScriptRunnerService(service.Service):

    def __init__(self, node_protocol, function):
        self.node_protocol = node_protocol
        self.function = function

    def startService(self):
        service.Service.startService(self)
        self.function(self.node_protocol)

    def stopService(self):
        service.Service.stopService(self)
