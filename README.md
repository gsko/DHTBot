DHTBot
======

DHTBot is a collection of utilities and protocols that help communicate
with nodes found in the BitTorrent MDHT network.

DHTBot is written entirely in Python using the asynchronous networking
framework Twisted.

The core functionality currently lies in the two twisted protocols found in
dhtbot/protocols/krpc_sender.py and dhtbot/protocols/krpc_responder.py

See examples/ for some examples on how to use these protocols.

Patches and suggestions are welcome!
