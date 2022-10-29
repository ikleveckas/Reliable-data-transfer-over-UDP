# Ignas Kleveckas s2095960

import sys
from socket import *
import time

if __name__ == '__main__':
    # receive input
    remote_host = sys.argv[1]
    port = int(sys.argv[2])
    file_name = (sys.argv[3])

    # configure socket
    so = socket(AF_INET, SOCK_DGRAM)
    so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    buffer_length = 1024

    # open file
    myfile = open(file_name, 'rb')
    data = myfile.read(buffer_length)
    data_len = len(data)

    # initialise header
    sequence_no = 0
    if len(data) < buffer_length:
        end_of_file = 1
    else:
        end_of_file = 0
    packet = bytearray(sequence_no.to_bytes(2, 'big'))
    packet.extend(end_of_file.to_bytes(1, 'big'))
    packet.extend(data)

    # send packets to receiver
    while data_len > 0:
        if so.sendto(bytes(packet), (remote_host, port)):
            data = myfile.read(buffer_length)
            data_len = len(data)
            sequence_no += 1
            if len(data) < buffer_length:
                end_of_file = 1
            packet = bytearray(sequence_no.to_bytes(2, 'big'))
            packet.extend(end_of_file.to_bytes(1, 'big'))
            packet.extend(data)
            time.sleep(0.01)
    
    # close sender
    so.close()
    myfile.close()
    print('finished transferring')
