# Ignas Kleveckas s2095960

import sys
from socket import *

if __name__ == '__main__':
    # receive port and filename
    port = int(sys.argv[1])
    file_name = (sys.argv[2])

    # configure socket
    so = socket(AF_INET, SOCK_DGRAM)
    so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    so.bind(('', port))
    
    # create file
    myfile = open(file_name, 'wb')

    # receive file
    packet, addr = so.recvfrom(1027)
    while packet:
            myfile.write(packet[3:])
            if packet[2] == 1:
                break
            packet,addr = so.recvfrom(1027)
    
    # close receiver
    myfile.close()
    so.close()
