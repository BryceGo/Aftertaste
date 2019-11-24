import copy
import json
from tools.dictionary import *
from tools.cipher import generateIV

class p_manager:
    def __init__(self,
                cipher_class,
                IV = '',
                CMD = '',
                PLD = ''):
        self.cipher_class = cipher_class
        self.IV = None

        self.packet = {}
        self.packet['END'] = END_FLAG_FALSE
        self.packet['IV'] = ''
        self.packet['CMD'] = ''
        self.packet['PLD'] = ''

        if CMD != '':
            self.store_command(CMD)
        if PLD != '':
            self.store_payload(PLD)
        if IV != '':
            self.store_iv(IV)

    def generate_IV(self):
        if self.IV == None:
            self.IV = generateIV()
            self.packet['IV'] = self.IV.hex()

    def clear(self):
        del self.packet
        cipher_class = self.cipher_class
        self.__init__(cipher_class = cipher_class)

    def store_end(self, end):
        self.packet['END'] = int(end)

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
        self.packet['CMD'] = command
        return True

    def store_payload(self, payload):
        if isinstance(payload, bytes):
            self.packet['PLD'] = payload.hex()
        elif isinstance(payload, str):
            self.packet['PLD'] = payload
        else:
            return False
        return True

    def encrypt_packet(self):
        self.generate_IV()
        self._encrypt_section('CMD')
        self._encrypt_section('PLD')

    def decrypt_packet(self):
        if self.IV == None:
            return False
        self._decrypt_section('CMD')
        self._decrypt_section('PLD')

    def _encrypt_section(self, section):
        self.packet[section] = self.cipher_class.encrypt(self.packet[section].encode(), self.IV).hex()

    def _decrypt_section(self, section):
        valid = self.cipher_class.decrypt(bytes.fromhex(self.packet[section]), self.IV)
        try:
            self.packet[section] = valid.decode()
        except:
            self.packet[section] = valid.hex()

    def is_last(self):
        return True if self.packet['END'] == 1 else False

    def concat(self, new_packet):
        if isinstance(new_packet, bytes):
            new_packet = json.loads(new_packet)
            self.packet['END'] += int(new_packet['END'])
            self.packet['PLD'] += new_packet['PLD']

    def load_packet(self, new_packet):
        if isinstance(new_packet, dict):
            self.store_end(new_packet['END'])
            self.store_iv(new_packet['IV'])
            self.store_command(new_packet['CMD'])
            self.store_payload(new_packet['PLD'])
        elif isinstance(new_packet, bytes):
            new_packet = json.loads(new_packet)
            self.store_end(new_packet['END'])
            self.store_iv(new_packet['IV'])
            self.store_command(new_packet['CMD'])
            self.store_payload(new_packet['PLD'])

    def get_packets(self):
        # Returns the packet as a form of a list
        returnList = []
        packet = copy.deepcopy(self.packet)
        leftover = packet['PLD']

        if len(leftover) <= MAX_PAYLOAD_LIMIT:
            packet['END'] = END_FLAG_TRUE
            returnList.append((json.dumps(packet)).encode())
            return returnList

        while(len(leftover) > MAX_PAYLOAD_LIMIT):
            packet['END'] = END_FLAG_FALSE
            leftover = packet['PLD'][MAX_PAYLOAD_LIMIT:]
            packet['PLD'] = packet['PLD'][:MAX_PAYLOAD_LIMIT]
            returnList.append((json.dumps(packet)).encode())

            packet = copy.deepcopy(packet)
            packet['PLD'] = leftover

        packet['END'] = END_FLAG_TRUE
        returnList.append((json.dumps(packet)).encode())
        return returnList