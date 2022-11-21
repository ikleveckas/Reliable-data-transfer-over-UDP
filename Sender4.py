# Ignas Kleveckas S2095960

import sys
import time
import os
import select
from socket import *
import heapq

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
        self.file_size = os.path.getsize(file_name)
        self.buffer_length = 1024
        self.total_packets = 1 + self.file_size / self.buffer_length
        self.timeout = False
        self.packets = [bytearray((0).to_bytes(1, 'big'))] #dummy value in 0 position
        self.heap = []
        self.received = [False] * (int(self.total_packets) + 1)
        
    def packet_monitor(self):
        while self.heap and self.retry_timeout - (time.time() - self.heap[0][0]) < 0:
            # if a packet was received remove it from heap
            if self.received[self.heap[0][1]]:
                heapq.heappop(self.heap)
            else:
                # resend packet and reset its timer
                head = self.heap[0]
                seqno = self.heap[0][1]
                self.so.sendto(self.packets[head[1]], (self.remote_host, self.port))
                heapq.heappushpop(self.heap, (time.time(), seqno))
            

    def receive(self):
        # check if there is an incoming packet
        ready = select.select([self.so], [], [], 0)
        if ready[0]:
            # if there is an incoming packet receive it
            response, addr = self.so.recvfrom(self.buffer_length)
            ack_no = int.from_bytes(response, 'big')
            # if the base packet was received, push the window forward
            if ack_no >= self.window_base:
                # until the next unacked packet
                self.received[ack_no] = True
                if ack_no == self.window_base:
                    while self.window_base < len(self.received) and self.received[self.window_base] == True:
                        self.window_base += 1

    def send_file(self):
        myfile = open(self.file_name, "rb")
        data = myfile.read(self.buffer_length)
        end_of_file = 0
        start = time.time()
        while self.window_base < self.total_packets or data:
            if self.sequence_no < self.window_base + self.window_size and data:

                # prepare header
                if len(data) < self.buffer_length:
                    end_of_file = 1
                else:
                    end_of_file = 0
                packet = bytearray(self.sequence_no.to_bytes(2, 'big'))
                packet.extend(end_of_file.to_bytes(1, 'big'))
                packet.extend(data)

                # send packet and add it to the packet heap
                self.packets.append(packet)
                self.so.sendto(packet, (self.remote_host, self.port))
                heapq.heappush(self.heap, (time.time(), self.sequence_no))

                self.sequence_no += 1

                # read data for the next packet
                data = myfile.read(self.buffer_length)
                if len(data) < self.buffer_length:
                    end_of_file = 1

            self.receive()
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