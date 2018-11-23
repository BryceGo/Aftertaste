import winreg, os, sys

def placeStartup(name ="HKEY_WINDOWS"):
	key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
	winreg.SetValueEx(key, name,0,winreg.REG_SZ,os.getcwd() + os.path.basename(sys.argv[0]))
	key.Close()