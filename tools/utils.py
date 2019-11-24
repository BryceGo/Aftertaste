from tools.packet_manager import *
from tools.cipher import *
from tools.dictionary import *
import time

def packet_send(command, payload, cipherClass, conn, encrypt=True):
    delay = SEND_DELAY
    pm = p_manager(cipherClass)
    pm.store_command(command)
    pm.store_payload(payload)
    if encrypt == True:
        pm.encrypt_packet()

    for i in pm.get_packets():
        conn.send(i)
        time.sleep(SEND_DELAY)

    del pm
    return True

def packet_recv(cipherClass, conn, decrypt=True):
    pm = p_manager(cipherClass)
    response = conn.recv(MAX_SOCK_RECV)
    pm.load_packet(response)
    while pm.is_last() == False:
        pm.concat(conn.recv(MAX_SOCK_RECV))
    if decrypt == True:
        pm.decrypt_packet()
    return pm.packet
