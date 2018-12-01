from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
import tools.cipher
import ftplib

class serverHandler(FTPHandler):

    def initHandler(self,key,IV):
        self.key = key
        self.IV = IV

    def on_file_received(self,file):
        print("Type of file is: {}".format(type(file)))
        print(file)

def ftpserver():
    authorizer = DummyAuthorizer()
    authorizer.add_anonymous('.')

    handler = serverHandler
    handler.authorizer = authorizer

    server = FTPServer(('0.0.0.0',5002),handler)
    server.serve_forever()

def ftpclient():
    ftp = ftplib.FTP('')
    ftp.connect('192.168.1.72',5002)
    ftp.login()