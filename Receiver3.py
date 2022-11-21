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
        #print('Receiving file...')
        sndpkt = (0).to_bytes(2, 'big')
        # receive file
        packet, sender_address = self.so.recvfrom(1027)
        while packet:
            received_seqno = int.from_bytes(packet[0:2], 'big')
            # check packet seq_no
            #print('Received packet. Seqno {0}. Expected seqno: {1}'.format(received_seqno, self.expectedseqno))
            if received_seqno == self.expectedseqno:
                # send ack
                sndpkt = self.expectedseqno.to_bytes(2, 'big')
                self.so.sendto(sndpkt, sender_address)

                # write data
                myfile.write(packet[3:])

                # update sequence_no
                self.expectedseqno += 1

                # check if end of file
                if packet[2] == 1:
                    #print('Received final packet. Download finished.')
                    # send more acks as per instructions in question @152 of comn piazza 
                    for i in range(15):
                        #sndpkt = self.expectedseqno.to_bytes(2, 'big')
                        self.so.sendto(sndpkt, sender_address)
                    
                    while True:
                        self.so.settimeout(2)
                        try:
                            packet, sender_address = self.so.recvfrom(1027)
                            received_seqno = int.from_bytes(packet[0:2], 'big')
                            #print('!! received a packet with seqno', received_seqno)
                            #ack = (self.expectedseqno).to_bytes(2, 'big')
                            self.so.sendto(sndpkt, sender_address)
                        except timeout:
                            break
                    break
            
            # handle all other cases
            else:
                # send ack
                #ack = (self.expectedseqno).to_bytes(2, 'big')
                self.so.sendto(sndpkt, sender_address)
                #print("Sent ACK with seqno ", int.from_bytes(ack, 'big'))
            # get next message
            packet, sender_address = self.so.recvfrom(1027)
        
        # close receiver
        myfile.close()
        self.so.close()
        

if __name__ == '__main__':
    receiver = Receiver(int(sys.argv[1]), sys.argv[2])  
    receiver.receive_file()