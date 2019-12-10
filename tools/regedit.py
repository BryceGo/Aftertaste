import winreg, os, sys
from tools.dictionary import SERVICE_NAME

# placeStartup
# Description:
# 	Adds itself to the registry startup run
# Parameters:
# 	name 				- the optional name of the registry value in startup
# Return:
# 	True				- Success
# 	False				- Failed
def placeStartup(name=SERVICE_NAME, root_path = os.getcwd()):
	try:
		key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
		winreg.SetValueEx(key, name,0,winreg.REG_SZ, root_path +"\\"+os.path.basename(sys.argv[0]))
		key.Close()
		return True
	except:
		return False

# removeStartup
# Description:
# 	Removes it's registry from the startup
# Parameters:
# 	name				- the optional name of the registry value (defaults to HKEY_WINDOWS)
# Return:
# 	True				- Success
# 	False				- Failed
def removeStartup(name=SERVICE_NAME):
	try:
		key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
		winreg.DeleteValue(key,name)
		key.Close()
		return True
	except:
		return False