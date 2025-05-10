import subprocess
import platform

def run_subprocess(cmd, **kwargs):
    if platform.system() == 'Windows':
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    return subprocess.run(cmd, **kwargs)

def popen_subprocess(cmd, **kwargs):
    if platform.system() == 'Windows':
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    return subprocess.Popen(cmd, **kwargs)