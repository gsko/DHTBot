"""
Twisted plugin that handles launching a daemonized version of DHTBot

This plugin handles starting the node protocol and wrapping it
with XMLRPC

"""
from zope.interface import implements
from twisted.python import log
from twisted.plugin import IPlugin

# need to import node service, xml rpc service
