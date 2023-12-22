#!/usr/bin/python3
import signal
from typing import List
import subprocess
from datetime import datetime
from multiprocessing.dummy import Pool # use threads
import time
import sys

procs: List[subprocess.Popen] = []

def receiveSignal(signalNumber, frame):
    if signal.SIGINT == signalNumber:
        for proc in procs:
            print(datetime.now(),"quit pid: ", proc.pid)
            try:
                out,err = proc.communicate(input='shutdown\n',timeout=3.0)
                print(out,err)
            except subprocess.TimeoutExpired:
                print(datetime.now(),"kill pid: ", proc.pid)
                proc.kill()




def pjsua(acc):
    args = [
        "pjsua",
        "--id=sip:" + acc[1] + "@" + acc[0],
        "--registrar=sip:" + acc[2],
        "--realm=*",
        "--username=" + acc[3],
        "--password=" + acc[4],
        "--local-port=" + str(acc[5]),
        "--no-tcp",
        "--no-vad",
        "--null-audio",
        "--auto-answer=200",
        "--use-cli",
        # "--no-cli-console",
        "--log-file=log/testpjsua_" + str(acc[5]) + ".log",
        "--log-level=4",
        "--app-log-level=0",
        "--duration=60",
    ]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.PIPE,
        universal_newlines=True,
        text=True,
        bufsize = 1
    )
    procs.append(proc)
    print(datetime.now(),"P:",proc.pid,args)


# list of domain, ext, registrar, username, password, port
accounts = [
    ["192.168.168.20", "102", "192.168.168.20", "cV2ucG5aUv", "HCxh9RhDqm", 6100],
    ["192.168.168.20", "103", "192.168.168.20", "iZ6Sau0NGd", "C3VbPlkIe8", 6104],
    ["192.168.168.20", "104", "192.168.168.20", "2vQ5uQuzMe", "4zfgLkbNzt", 6108],
    ["192.168.168.20", "105", "192.168.168.20", "cUjH3PbN3u", "lbkpx8Ac1M", 6112],
    ["192.168.168.20", "106", "192.168.168.20", "cqDSpRO89z", "7rfaacFRkf", 6116],
]

def main(argv):
    for acc in accounts:
        pjsua(acc)
    print("all started with pids: ", [p.pid for p in procs])
    print("all exited with codes: ", [p.wait() for p in procs])

if __name__ == '__main__':
    signal.signal(signal.SIGINT, receiveSignal)
    main(sys.argv[1:])

# chmod +x testsua.py
# nohup sudo ./testsua.py &
# sudo ps -x | grep sudo.*testsua | awk '{print $1}' | xargs sudo kill -s INT
