DHTBot
======

DHTBot is a collection of utilities and protocols that help communicate
with nodes found in the BitTorrent MDHT network.

DHTBot is written entirely in Python using the asynchronous networking
framework Twisted. The Bencode algorithm implementation is taken from the last
open source version of the BitTorrent client.

DHTBot can act as a standalone BEP5 BitTorrent DHT client. Development for
DHTBot is still in the beta stage with missing features. The goal of this
project is to provide a simple interface for a user to query/poll the DHT
network and examine the results.

* The dhtbot folder contains all the source files. Most of the modules found
    in this folder should contain docstrings describing their usage. The
    core functionality of DHTBot is currently found in the two protocols found
    in dhtbot/protocols/krpc_sender.py and dhtbot/protocols/krpc_responder.py
* The license folder contains the bittorrent license (for the bencode.py).
    And will be used to hold licenses for various libraries used in this
    project.
* The examples folder contains a few short examples of how to use the
    twisted protocols. See the twisted documentation
    (http://www.twistedmatrix.com) for more help on twisted.
* The references folder contains a few pdf's and html files of DHT
    research and specifications that were used in the development of DHTBot


The core functionality currently lies in the two twisted protocols found in
dhtbot/protocols/krpc_sender.py and dhtbot/protocols/krpc_responder.py

Patches and suggestions are welcome!
Send your contributions to gsk067@gmail.com
