# Ignas Kleveckas S2095960

import sys
import time
import os
import select
from socket import *

class Sender(object):
    def __init__(self, remote_host, port, file_name, retry_timeout, window_size):
        # receive input
        self.remote_host = remote_host
        self.port = port
        self.file_name = file_name
        self.retry_timeout = retry_timeout / 1000
        self.window_size = window_size

        # configure socket
        self.so = socket(AF_INET, SOCK_DGRAM)

        # initialise remaining values
        self.sequence_no = 1
        self.window_base = 1
        self.transfer_time = 0
        self.file_size = os.path.getsize(file_name)
        self.buffer_length = 1024
        self.total_packets = 1 + (self.file_size / self.buffer_length)
        self.timeout = False
        self.timer = False
        self.packets = [bytearray((0).to_bytes(1, 'big'))] #dummy value in 0 position
        

    def packet_monitor(self):
        if not self.timeout:
            time_left = self.retry_timeout - (time.time() - self.time_sent)
            if time_left >= 0:
                
                # check if there is an incoming packet
                ready = select.select([self.so], [], [], 0)
                if ready[0]:
                    self.receive()
            else:
                self.timeout = True
        else:
            self.process_timeout()

    def receive(self):
        response, addr = self.so.recvfrom(self.buffer_length)
        ack_no = int.from_bytes(response, 'big')
        #print("ACK received " + str(ack_no))
        self.window_base = ack_no + 1

        # if the ack for the base packet was received, stop the timer
        if self.window_base == self.sequence_no:
            self.timer = False

        # otherwise reset the timer
        else:
            self.time_sent = time.time()
            self.timer = True

    def process_timeout(self):
        self.timer = True
        self.timeout = False
        self.time_sent = time.time()

        # resend the packets in the window (after window base)
        for i in range(self.window_base, self.sequence_no):
            packet = self.packets[i]
            self.so.sendto(packet, (self.remote_host, self.port))
            #print("Packet retransmitted " + str(i))
            

    def send_file(self):
        myfile = open(self.file_name, "rb")
        data = myfile.read(self.buffer_length)
        end_of_file = 0
        start = time.time()
        while self.window_base < self.total_packets or data:
            #if time.time() - start > 180: # TESTING
                #break
            if self.sequence_no < self.window_base + self.window_size and data:

                # prepare header
                if len(data) < self.buffer_length:
                    end_of_file = 1
                else:
                    end_of_file = 0
                packet = bytearray(self.sequence_no.to_bytes(2, 'big'))
                packet.extend(end_of_file.to_bytes(1, 'big'))
                packet.extend(data)

                # send packet and add it to the packet list
                self.packets.append(packet)
                self.so.sendto(packet, (self.remote_host, self.port))
                #print("Packet sent " + str(self.sequence_no))

                # if sending the base packet, start the timer
                if self.window_base == self.sequence_no:
                    self.time_sent = time.time()
                    self.timer = True

                self.sequence_no += 1

                # read data for the next packet
                data = myfile.read(self.buffer_length)
                if len(data) < self.buffer_length:
                    end_of_file = 1

            if self.timer:
                self.packet_monitor()

        total_time = time.time() - start
        throughput = self.file_size / (1000 * total_time)
        print(throughput)

        # close the file and socket
        self.so.close()
        myfile.close()

        return throughput

if __name__ == '__main__':
    sender = Sender(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    sender.send_file()