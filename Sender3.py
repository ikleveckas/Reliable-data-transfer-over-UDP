# Ignas Kleveckas s2095960
import sys
from socket import *
from threading import Thread
from threading import Lock
from typing import OrderedDict
import select

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
        self.so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # initialise remaining values
        self.sequence_no = 0
        self.rentransmissions = 0
        self.transfer_time = 0
        self.file_size = 0
    
    def send_file(self):
        lock = Lock()
        window = Window(self.window_size, lock)
        packet_sender = PacketSender(self.file_name, self.so, (self.remote_host, self.port),
        window, self.retry_timeout, lock)
        ack_receiver = AckReceiver(self.so, window, self.retry_timeout, lock)
        packet_sender.start()
        ack_receiver.start()
        packet_sender.join()
        ack_receiver.join()
        self.so.close()


class Window(object):
    def __init__(self, window_size, lock):
        self.window_size = window_size
        self.finished = False
        self.base = 1
        self.nextseqnum = 1
        self.lock = lock
    
    def empty(self):
        return self.base == self.nextseqnum

    def full(self):
        return self.nextseqnum >= self.base + self.window_size

    def ack(self, seq_no):
        self.lock.acquire()
        self.base = seq_no + 1
        self.lock.release()

    def clear(self):
        self.nextseqnum = self.base


class PacketSender(Thread):
    def __init__(self, file_name, socket, receiver_address, window, timeout, lock):
        self.file_name = file_name
        self.buffer_length = 1024
        self.file_size = 0
        self.so = socket
        self.receiver_address = receiver_address
        self.window = window
        self.timeout = timeout
        self.lock = lock
        Thread.__init__(self)

    def run(self):
        packets = self.read_file()
        packet = packets[0] # might be empty file check if raises an error!
        print('Started sending')
        while True:
            if self.window.base >= len(packets):
                self.window.finished = True
                break
            if self.window.full() or self.window.nextseqnum >= len(packets):
                continue
            self.lock.acquire()
            packet = packets[self.window.nextseqnum]
            if self.window.empty() or not self.so.gettimeout():
                self.so.settimeout(self.timeout)    
                print('Timer set from nothing!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!.')
            print('Packet sent with seqnum {0}, while base is {1}'.format(self.window.nextseqnum, self.window.base))
            self.so.sendto(packet, self.receiver_address)
            self.window.nextseqnum += 1
            self.lock.release()
        print('Finished sending')


    def read_file(self):
        myfile = open(self.file_name, 'rb')
        i = 1
        packets = [bytearray((0).to_bytes(1, 'big'))] #dummy value in 0 position
        while True:
            data = myfile.read(self.buffer_length)
            if len(data) == 0:
                break
            self.file_size += len(data)
            if len(data) < self.buffer_length:
                end_of_file = 1
            else:
                end_of_file = 0
            packet = bytearray((i).to_bytes(2, 'big'))
            packet.extend(end_of_file.to_bytes(1, 'big'))
            packet.extend(data)
            packets.append(packet)
            i += 1
        
        return packets
        


            

class AckReceiver(Thread):
    def __init__(self, so, window, timeout, lock):
        self.so = so
        self.window = window
        self.timeout = timeout
        self.lock = lock
        Thread.__init__(self)

    def run(self):
        while not self.window.finished:
            if self.window.empty():
                continue

            if self.window.full():
                self.lock.acquire()
                self.listen()
                self.lock.release()
            
            else:
                self.listen()


    def listen(self):
        try:
            response, addr = self.so.recvfrom(2)
            self.window.base = int.from_bytes(response[0:2], 'big') + 1
            print('Received ACK with seq no {0}. New base = {1}'.format(int.from_bytes(response[0:2], 'big'), self.window.base))
            if self.window.empty():
                print('Timer stopped.')
                self.so.settimeout(None)
            else:
                print('Timer set.')
                self.so.settimeout(self.timeout)
        except timeout:
            print('Timeout. Resetting timer.')
            self.so.settimeout(self.timeout)
            self.window.clear()
        
            """
            
            ready = select.select([self.so], [], [], self.timeout)
            if not ready[0]:
                self.window.clear()
                continue

            else:
                response, address = self.so.recvfrom(2)
                response_seq_no = int.from_bytes(response[0:2], 'big')
                self.window.ack(response_seq_no)

            """
if __name__ == '__main__':
    sender = Sender(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    sender.send_file()

