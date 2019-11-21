import copy
import json
from dictionary import *

class packet:
    def __init__(self,
                IV=None,
                CMD = None,
                PLD = None):
        self.packet = {}
        self.packet['IV'] = IV
        self.packet['CMD'] = CMD
        self.packet['PLD'] = PLD
        self.packet['END'] = END_FLAG_TRUE
        # self.packet['LEN'] = 0

    def clear(self):
        self.__init__()

    def store_iv(self, IV):
        if isinstance(IV, bytes):
            self.packet['IV'] = str(IV.hex())
        elif isinstance(IV, string):
            self.packet['IV'] = IV
        else:
            return False
        return True

    def store_command(self, command):
        self.packet['CMD'] = command

    def store_payload(self, payload):
        if isinstance(payload, bytes):
            self.packet['PLD'] = payload.hex()
        elif isinstance(payload, string):
            self.packet['PLD'] = payload
        else:
            return False
        return True

    def get_packet(self):
        return json.dumps(copy.deepcopy(self.packet)).encode()
