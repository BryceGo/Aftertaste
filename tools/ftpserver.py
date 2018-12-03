from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
import settings.keys as keys
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
    for i in range(0,len(keys.USER)):
        authorizer.add_user(keys.USER[i],keys.PASSWORD[i],keys.SERVER_DIR,perm='w')

    handler = serverHandler
    handler.authorizer = authorizer

    server = FTPServer((keys.IP_ADDRESS_SERVER,keys.PORT),handler)
    server.serve_forever()

def ftpUpload(fileName):
    ftp = ftplib.FTP('')
    ftp.connect(keys.IP_ADDRESS_CLIENT,keys.PORT)
    ftp.login(keys.USER[0],keys.PASSWORD[0])
    ftp.storbinary('STOR '+fileName,open(fileName,'rb'))
    ftp.quit()
    return