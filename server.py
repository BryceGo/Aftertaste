import socket, threading, time, sys
import _thread as thread
import subprocess
import tools.cipher as cipher
import settings.keys as keys
import json
from tools.packet_manager import p_manager
import time
from tools.dictionary import SEND_DELAY, MAX_SOCK_RECV
from tools.utils import packet_send, packet_recv

class baseServer():
    def __init__(self, port, listen=1):
        self.connection_lock = thread.allocate_lock()
        self.connection_list = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(3)
        self.sock.bind(('0.0.0.0',port))
        self.sock.listen(listen)

    def listen_connections(self):
        while(True):
            try:
                self.connection = self.sock.accept()
            except socket.timeout:
                continue
            print("Obtained a new connection...")

            self.connection_lock.acquire()
            self.connection_list.append(self.connection)
            self.connection_lock.release()

    def receiver(self, conn, cipherClass):
        while(True):
            try:
                packet = packet_recv(cipherClass=cipherClass,
                            conn=conn,
                            decrypt=True)
            except:
                continue
            print(packet['PLD'])

    def sender(self, conn, cipherClass):
        while(True):
            command = input()
            if len(command) <= 0:
                continue
            try:
                packet_send(command='CMD',
                            payload=command,
                            cipherClass=cipherClass,
                            conn=conn,
                            encrypt=True)
            except Exception as e:
                print("Error sending command.")


    def authenticate(self, conn, cipherClass):
        while(True):
            try:
                password = cipher.generateIV().hex()
                packet_send(command="SRT",
                            payload=password,
                            cipherClass=cipherClass,
                            conn=conn)


                packet = packet_recv(cipherClass=cipherClass,
                            conn=conn,
                            decrypt=False)

                if packet["CMD"] == "ACK" and packet["PLD"] == password:
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

        if (self.authenticate(connection[0], cipherClass) == False):
            return

        receiver = threading.Thread(target=self.receiver,args=(connection[0],cipherClass))
        sender = threading.Thread(target=self.sender,args=(connection[0],cipherClass))

        receiver.start()
        sender.start()

    def __del__(self):
        self.sock.close()

if __name__ == "__main__":
    PORT = int(sys.argv[1])
    print("Creating server on port: {}".format(PORT))
    server = baseServer(PORT)
    listener = threading.Thread(target=server.listen_connections)
    listener.start()
    while(len(server.connection_list) <= 0):
        pass

    server.connection_lock.acquire()
    connection = server.connection_list.pop(0)
    server.connection_lock.release()
    server.startConnection(connection)

    while(True):
        pass
