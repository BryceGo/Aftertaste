import copy
import json
from tools.dictionary import *
from tools.cipher import generateIV
from tools.dictionary import *

class p_manager:
    def __init__(self,
                cipher_class,
                IV = '',
                CMD = '',
                PLD = ''):
        self.cipher_class = cipher_class
        self.IV = None

        self.packet = {}
        self.packet[PK_END_FLAG] = END_FLAG_FALSE
        self.packet[PK_IV_FLAG] = ''
        self.packet[PK_COMMAND_FLAG] = ''
        self.packet[PK_PAYLOAD_FLAG] = ''

        if CMD != '':
            self.store_command(CMD)
        if PLD != '':
            self.store_payload(PLD)
        if IV != '':
            self.store_iv(IV)

    def generate_IV(self):
        if self.IV == None:
            self.IV = generateIV()
            self.packet[PK_IV_FLAG] = self.IV.hex()

    def clear(self):
        del self.packet
        cipher_class = self.cipher_class
        self.__init__(cipher_class = cipher_class)

    def store_end(self, end):
        self.packet[PK_END_FLAG] = int(end)

    def store_iv(self, IV):
        if isinstance(IV, bytes):
            self.packet[PK_IV_FLAG] = str(IV.hex())
            self.IV = IV
        elif isinstance(IV, str):
            self.packet[PK_IV_FLAG] = IV
            self.IV = bytes.fromhex(IV)
        else:
            return False
        return True

    def store_command(self, command):
        self.packet[PK_COMMAND_FLAG] = command
        return True

    def store_payload(self, payload):
        if isinstance(payload, bytes):
            self.packet[PK_PAYLOAD_FLAG] = payload.hex()
        elif isinstance(payload, str):
            self.packet[PK_PAYLOAD_FLAG] = payload
        else:
            return False
        return True

    def encrypt_packet(self):
        self.generate_IV()
        self._encrypt_section(PK_COMMAND_FLAG)
        self._encrypt_section(PK_PAYLOAD_FLAG)

    def decrypt_packet(self):
        if self.IV == None:
            return False
        self._decrypt_section(PK_COMMAND_FLAG)
        self._decrypt_section(PK_PAYLOAD_FLAG)

    def _encrypt_section(self, section):
        self.packet[section] = self.cipher_class.encrypt(self.packet[section].encode(), self.IV).hex()

    def _decrypt_section(self, section):
        valid = self.cipher_class.decrypt(bytes.fromhex(self.packet[section]), self.IV)
        try:
            self.packet[section] = valid.decode('utf-8')
        except:
            self.packet[section] = valid.hex()

    def is_last(self):
        return True if self.packet[PK_END_FLAG] == 1 else False

    def concat(self, new_packet):
        if isinstance(new_packet, bytes):
            new_packet = json.loads(new_packet)
            self.packet[PK_END_FLAG] += int(new_packet[PK_END_FLAG])
            self.packet[PK_PAYLOAD_FLAG] += new_packet[PK_PAYLOAD_FLAG]

    def load_packet(self, new_packet):
        if isinstance(new_packet, dict):
            self.store_end(new_packet[PK_END_FLAG])
            self.store_iv(new_packet[PK_IV_FLAG])
            self.store_command(new_packet[PK_COMMAND_FLAG])
            self.store_payload(new_packet[PK_PAYLOAD_FLAG])
        elif isinstance(new_packet, bytes):
            new_packet = json.loads(new_packet)
            self.store_end(new_packet[PK_END_FLAG])
            self.store_iv(new_packet[PK_IV_FLAG])
            self.store_command(new_packet[PK_COMMAND_FLAG])
            self.store_payload(new_packet[PK_PAYLOAD_FLAG])

    def get_packets(self):
        # Returns the packet as a form of a list
        returnList = []
        packet = copy.deepcopy(self.packet)
        leftover = packet[PK_PAYLOAD_FLAG]

        if len(leftover) <= MAX_PAYLOAD_LIMIT:
            packet[PK_END_FLAG] = END_FLAG_TRUE
            returnList.append((json.dumps(packet)).encode())
            return returnList

        while(len(leftover) > MAX_PAYLOAD_LIMIT):
            packet[PK_END_FLAG] = END_FLAG_FALSE
            leftover = packet[PK_PAYLOAD_FLAG][MAX_PAYLOAD_LIMIT:]
            packet[PK_PAYLOAD_FLAG] = packet[PK_PAYLOAD_FLAG][:MAX_PAYLOAD_LIMIT]
            returnList.append((json.dumps(packet)).encode())

            packet = copy.deepcopy(packet)
            packet[PK_PAYLOAD_FLAG] = leftover

        packet[PK_END_FLAG] = END_FLAG_TRUE
        returnList.append((json.dumps(packet)).encode())
        return returnList