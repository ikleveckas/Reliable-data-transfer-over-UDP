# Ignas Kleveckas s2095960

import sys
from socket import *
from time import time
from timeit import default_timer as timer

class Sender(object):
    def __init__(self, remote_host, port, file_name, retry_timeout):
        # receive input
        self.remote_host = remote_host
        self.port = port
        self.file_name = file_name
        self.retry_timeout = retry_timeout / 1000

        # configure socket
        self.so = socket(AF_INET, SOCK_DGRAM)
        self.so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # initialise remaining values
        self.buffer_length = 1024
        self.sequence_no = 0
        self.rentransmissions = 0
        self.transfer_time = 0
        self.file_size = 0

    def send_file(self):
        # open file
        myfile = open(self.file_name, 'rb')
        start = timer() # start measuring time before first transmission
        while True:
            data = myfile.read(self.buffer_length)
            self.file_size += len(data)
            # if there is nothing more to read
            if len(data) == 0:
                break
            # prepare header
            if len(data) < self.buffer_length:
                end_of_file = 1
            else:
                end_of_file = 0
            message = bytearray(self.sequence_no.to_bytes(2, 'big'))
            message.extend(end_of_file.to_bytes(1, 'big'))
            message.extend(data)

            # send message
            response = self.send_and_wait(message)
            while int.from_bytes(response, 'big') != self.sequence_no:
                response = self.send_and_wait(message)
            if end_of_file == 1:
                end = timer() # stop timer after ack receipt for last message
            self.sequence_no += 1
        
        # shut down
        #print("Transfer finished")
        self.transfer_time = end - start
        self.so.close()
        myfile.close()
    
    def send_and_wait(self, message):
        #print('sending: ',self.sequence_no)
        self.so.sendto(bytes(message), (self.remote_host, self.port))
        self.so.settimeout(self.retry_timeout)
        try:
            response, addr = self.so.recvfrom(2)
            #print('received: ', int.from_bytes(response, 'big'))
            return response
        except timeout:
            #print('timeout')
            self.rentransmissions += 1
            self.so.settimeout(self.retry_timeout)
            return self.send_and_wait(message)


if __name__ == '__main__':
    sender = Sender(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
    sender.send_file()
    print("{0} {1}".format(sender.rentransmissions, sender.file_size / (sender.transfer_time * 125)))