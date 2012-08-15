"""
Functions common to both the xml_rpc client and server (such as en/de coding)
"""
import pickle

def inflate(data):
    return pickle.loads(data)

def deflate(data):
    return pickle.dumps(data)
