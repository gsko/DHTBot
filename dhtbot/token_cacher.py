#
# Author: Greg Skoczek
#
import time
from collections import defaultdict

from twisted.internet import reactor

from dhtbot import constants



class TokenCacher(object):

    def __init__(self):
        self.tokencache = defaultdict(dict)

    def cache(self, query, response, address):
        target_id = query.target_id
        token = response.token
        now = time.time()
        self.tokencache[target_id][address] = (token, now)
        reactor.callLater(constants.token_timeout,
                          self.prunetoken, target_id, address)

    def prunetoken(self, target_id, address):

        if (target_id in self.tokencache and
            address in self.tokencache[target_id]):
               (token, insert_time) = self.tokencache[target_id][address]
               now = time.time()
               age = now - insert_time
               if age >= constants.token_timeout:
                   del self.tokencache[target_id][address]
                   if len(self.tokencache[target_id]) == 0:
                       del self.tokencache[target_id]

    def get_tokens(self, target_id):
        if target_id in self.tokencache:
            # TODO check proper indentation standards
            tokens = [(token, address) for (address, (token, insert_time))
                               in self.tokencache[target_id].iteritems()]
            return tokens
