import copy
import json
from tools.dictionary import *

class packet:
    def __init__(self,
                cipher_class,
                IV=None,
                CMD = None,
                PLD = None):
        self.cipher_class = cipher_class
        self.IV = None

        self.packet = {}
        self.packet['END'] = END_FLAG_FALSE
        self.packet['IV'] = None
        self.packet['CMD'] = None
        self.packet['PLD'] = None

        self.store_iv(IV)
        self.store_command(CMD)
        self.store_payload(PLD)



        # self.packet['LEN'] = 0

    def check_IV(self):
        return True if self.packet['IV'] != None else False

    def clear(self):
        del self.packet
        cipher_class = self.cipher_class
        self.__init__(cipher_class = cipher_class)

    def store_iv(self, IV):
        if isinstance(IV, bytes):
            self.packet['IV'] = str(IV.hex())
            self.IV = IV
        elif isinstance(IV, str):
            self.packet['IV'] = IV
            self.IV = bytes.fromhex(IV)
        else:
            return False
        return True

    def store_command(self, command):
        if self.check_IV():
            encrypted_command = self.cipher_class.encrypt(command.encode(), self.IV).hex()
            self.packet['CMD'] = encrypted_command
            return True
        else:
            return False

    def store_payload(self, payload):
        if not(self.check_IV()):
            return False
        if isinstance(payload, bytes):
            self.packet['PLD'] = payload.hex()
        elif isinstance(payload, str):
            self.packet['PLD'] = payload
        else:
            return False

        self.packet['PLD'] = self.cipher_class.encrypt(payload.encode(), self.IV).hex()

        return True

    def get_packet(self):
        # Returns the packet as a form of a list
        returnList = []
        packet = copy.deepcopy(self.packet)
        leftover = packet['PLD']

        if len(leftover) <= MAX_PAYLOAD_LIMIT:
            packet['END'] = END_FLAG_TRUE
            returnList.append((json.dumps(packet).replace(' ','')).encode())
            return returnList

        while(len(leftover) > MAX_PAYLOAD_LIMIT):
            packet['END'] = END_FLAG_FALSE
            leftover = packet['PLD'][MAX_PAYLOAD_LIMIT:]
            packet['PLD'] = packet['PLD'][:MAX_PAYLOAD_LIMIT]
            returnList.append((json.dumps(packet).replace(' ','')).encode())

            packet = copy.deepcopy(packet)
            packet['PLD'] = leftover

        packet['END'] = END_FLAG_TRUE
        returnList.append((json.dumps(packet).replace(' ','')).encode())
        return returnList