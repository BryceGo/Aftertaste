import socket, threading, time, sys
import _thread as thread
import subprocess
import tools.cipher as cipher

class baseServer():
    def __init__(self, port, listen=1):
        self.connection_lock = thread.allocate_lock()
        self.connection_list = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(3)
        self.sock.bind(('',port))
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

    def receiver(self, conn):
        while(True):
            response = conn.recv(2048).decode()
            print(response)

    def sender(self, conn):
        while(True):
            command = input()
            conn.send(command.encode())

    def startConnection(self, connection):
        #Enter Needed connection to start
        while(True):
            try:
                IV = cipher.generateIV()
                connection[0].send('SRT'.encode()+IV)
                response = connection[0].recv(2048)
                if (response[3:]==IV):
                    break
                else:
                    print("Configuration error. Socket returned a different Initialization Vector")
                    continue
            except socket.timeout:
                continue
            except:
                print("Error, connection from client lost.")
                return

        receiver = threading.Thread(target=self.receiver,args=(connection[0],))
        sender = threading.Thread(target=self.sender,args=(connection[0],))

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
