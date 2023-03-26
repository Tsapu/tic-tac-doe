import socket
from contextlib import closing
   
def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, int(port))) == 0:
            return True
        else:
            return False