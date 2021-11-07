import os
import sys
import time

pip_path = "\\".join(sysexec for sysexec in sys.executable.split('\\')[:len(sys.executable.split('\\')) - 1]) + '\\Scripts\\pip.exe'
cwd = os.getcwd()

import subprocess

subprocess.call(pip_path + ' install -r requirements.txt')

import win32gui
import win32con

#win32gui.ShowWindow(win32gui.GetForegroundWindow(), win32con.SW_HIDE)

import services
import connection

root_update = services.RootUpdate()
root_update.start()

