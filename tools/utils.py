from tools.packet_manager import *
from tools.cipher import *
from tools.dictionary import *
from tools.exception_handler import exception_handler
from os.path import basename
import time
import json

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