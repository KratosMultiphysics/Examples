import os
import sys
import pathlib
import subprocess

rootdir = "."
current = os.getcwd()

for subdir, dirs, files in os.walk(rootdir):
    for filename in files:
        p = pathlib.PurePath(current, subdir, filename)
        
        if p.name == "MainKratos.py":
            sp = subprocess.Popen([sys.executable, p], cwd=p.parents[0])
            x = sp.wait()

            print("Exit with code", x)