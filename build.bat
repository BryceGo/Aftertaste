rmdir /q /s dist
pyinstaller .\client.py --onefile -w --icon=windows.ico
ren dist\client.exe ServiceExecutable.exe
pause