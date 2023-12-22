import psutil
import re

def KillProcess(name, arg_match = None):
    if arg_match:
        pattern = re.compile(arg_match)
    for pi in psutil.process_iter():
        if pi.name() == name:
            try:
                for arg in pi.cmdline():
                    if arg_match is None or re.search(pattern,arg):
                        p = psutil.Process(pi.pid)
                        # p.kill()
                        print("killed process", pi.pid)
                        break
            except Exception as err:
                pass