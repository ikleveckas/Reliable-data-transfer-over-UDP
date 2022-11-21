# Ignas Kleveckas s2095960

import sys
from socket import *
import time

class Receiver(object):
    def __init__(self, port, file_name, window_size):
        # receive input
        self.port = port
        self.file_name = file_name
        self.window_size = window_size

        # configure socket
        self.so = socket(AF_INET, SOCK_DGRAM)
        self.so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.so.bind(('', self.port))
        self.expected_seqno = 1
        self.buffer = {}

    def receive_file(self):
        # create file
        myfile = open(self.file_name, 'wb')
        ack = (0).to_bytes(2, 'big')
        # receive file
        packet, sender_address = self.so.recvfrom(1027)
        last_val = 1 # marks the last seq no of the whole file
        while True:
            last = packet[2] == 1
            received_seqno = int.from_bytes(packet[0:2], 'big')
            last_val = max(last_val, received_seqno)
            # check message seq_no
            # check if packet falls within window
            if received_seqno in range(self.expected_seqno, self.expected_seqno + self.window_size):
                # If the packet was not previously received, it is buffered
                if not received_seqno in self.buffer:
                    self.buffer[received_seqno] = packet

                # send a selective ack
                ack = received_seqno.to_bytes(2, 'big')
                self.so.sendto(ack, sender_address)

                if received_seqno == self.expected_seqno:
                    # consecutively numbered packets are written
                    while (self.expected_seqno in self.buffer):
                        myfile.write(self.buffer[self.expected_seqno][3:])
                        last = last or self.buffer[self.expected_seqno][2] == 1
                        self.buffer.pop(self.expected_seqno)
                        self.expected_seqno += 1

                    # check if this packet was required to finish downloading
                    if last:
                        for j in range(10):
                            self.so.sendto(ack, sender_address)

                        # ensure that the sender has ACKs for all packets before terminating
                        while True:
                            self.so.settimeout(2)
                            try:
                                packet, sender_address = self.so.recvfrom(1027)
                                received_seqno = int.from_bytes(packet[0:2], 'big')
                                ack = (received_seqno).to_bytes(2, 'big')
                                self.so.sendto(ack, sender_address)
                            except timeout:
                                break
                        break
                
            # reacknowledge recently received packages if they are duplicate
            elif received_seqno in range(self.expected_seqno - self.window_size, self.expected_seqno):
                # send ack
                ack = (received_seqno).to_bytes(2, 'big')
                self.so.sendto(ack, sender_address)

            # otherwise the packet is ignored

            # get next message
            packet, sender_address = self.so.recvfrom(1027)
        
        # close receiver
        myfile.close()
        self.so.close()
        

if __name__ == '__main__':
    receiver = Receiver(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))  
    receiver.receive_file()