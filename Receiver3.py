# Ignas Kleveckas s2095960

import sys
from socket import *

class Receiver(object):
    def __init__(self, port, file_name):
        # receive port and filename
        self.port = port
        self.file_name = file_name

        # configure socket
        self.so = socket(AF_INET, SOCK_DGRAM)
        self.so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.so.bind(('', self.port))
        self.expectedseqno = 1

    def receive_file(self):
        # create file
        myfile = open(self.file_name, 'wb')
        print('Receiving file...')
        ack = (0).to_bytes(2, 'big')
        # receive file
        message, sender_address = self.so.recvfrom(1027)
        while message:
            # check message seq_no
            print('Received packet. Seqno {0}. Expected seqno: {1}'.format(int.from_bytes(message[0:2], 'big'), self.expectedseqno))
            if int.from_bytes(message[0:2], 'big') == self.expectedseqno:
                # write data
                myfile.write(message[3:])

                # send ack
                ack = self.expectedseqno.to_bytes(2, 'big')
                self.so.sendto(ack, sender_address)

                # update sequence_no
                self.expectedseqno += 1

                # check if end of file
                if message[2] == 1:
                    print('Received final packet. Download finished.')
                    # send more acks as per instructions in question @152 of comn piazza 
                    for i in range(15):
                        ack = self.expectedseqno.to_bytes(2, 'big')
                        self.so.sendto(ack, sender_address)
                    break
            
            # handle all other cases
            else:
                # send ack
                #ack = (self.expectedseqno).to_bytes(2, 'big')
                self.so.sendto(ack, sender_address)
                print("Sent ACK with seqno ", int.from_bytes(ack, 'big'))
            # get next message
            message, sender_address = self.so.recvfrom(1027)
        
        # close receiver
        myfile.close()
        self.so.close()
        

if __name__ == '__main__':
    receiver = Receiver(int(sys.argv[1]), sys.argv[2])  
    receiver.receive_file()