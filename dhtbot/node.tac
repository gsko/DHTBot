#
# Author: Greg Skoczek
#

from twisted.application import internet, service

from dhtbot.services.niceservice import NICEService 
from dhtbot.services.script_runner import ScriptRunnerService
from dhtbot.protocols.krpc_sender import KRPC_Sender
from dhtbot.protocols.simple_node_protocol import SimpleNodeProtocol
from dhtbot.scripts import basic_tester


application = service.Application("node")

udp_port = 1800
startup_function = basic_tester.startup

# TODO for debugging purposes
node = SimpleNodeProtocol(354964679750869290640294479805992621239480307655)
nice_service = NICEService(node)
node_service = internet.UDPServer(udp_port, node)
scriptrunner_service = ScriptRunnerService(node, startup_function)

ms_node_service = service.MultiService()
ms_nice_service = service.MultiService()
ms_scriptrunner_service = service.MultiService()

nice_service.setServiceParent(ms_nice_service)

ms_nice_service.setServiceParent(ms_node_service)
node_service.setServiceParent(ms_node_service)

ms_node_service.setServiceParent(ms_scriptrunner_service)
scriptrunner_service.setServiceParent(ms_scriptrunner_service)

ms_scriptrunner_service.setServiceParent(application)
