import socket, threading, time
import _thread as thread
import subprocess

PORT = 5001

class baseServer():
    def __init__(self, port, listen=1):
        self.connection_lock = thread.allocate_lock()
        self.connection_list = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('',port))
        self.sock.listen(listen)

    def listen_connections(self):
        while(True):
            print("waiting for connection....")
            self.connection = self.sock.accept()

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
    def __del__(self):
        self.sock.close()


if __name__ == "__main__":
    server = baseServer(PORT)
    listener = threading.Thread(target=server.listen_connections)
    listener.start()
    while(len(server.connection_list) <= 0):
        pass

    server.connection_lock.acquire()
    connection = server.connection_list.pop(0)
    server.connection_lock.release()

    receiver = threading.Thread(target=server.receiver,args=(connection[0],))
    sender = threading.Thread(target=server.sender,args=(connection[0],))
    print("Ready...")

    receiver.start()
    sender.start()
    while(True):
        pass
