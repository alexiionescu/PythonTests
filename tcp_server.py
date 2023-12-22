# %%
import string
import time
import socket
port = input("Please enter the bind port (Default 12456)\n")
if len(port) == 0:
    port = 12456
def test_server():
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    address = ('', int(port)) 
    server.bind(address)
    server.listen(10)
    print("Listen on ", address)
    keepRunning = True
    while keepRunning:
        s,addr=server.accept()
        print("Connected from ", addr)
        while 1:
            data = s.recv(2048)
            if len(data) == 0:
                break 
            print (data)
            if data.decode("utf-8").startswith("shutdown"):
                keepRunning = False
                break
        s.close()
        print("Disconnected from ", addr)
print('Shutdown received.Bye.')
test_server()