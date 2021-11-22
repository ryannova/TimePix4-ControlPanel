import socket
import threading
import time
import queue

HEADER_SIZE = 4
FRAME_SIZE = 128*128
PACKET_SIZE = HEADER_SIZE + FRAME_SIZE

class tp4():

    def __init__(self, host="127.0.0.1", port=2686, buffer_size=1000):
        self.packet_buffer = queue.Queue(maxsize=buffer_size)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


        
        self.pc = threading.Thread(target=self.packet_capture)
        self.pkt_in_buffer = threading.Event()

        self.sock.bind((host, port))
        #self.sp = threading.Thread(target=self.saving_packets)
        self.pc.start()
        #self.sp.start()
    

    def packet_capture(self):
        while True:
            packet = self.sock.recvfrom(PACKET_SIZE)
            self.packet_buffer.put(packet[0])
    
    def read_packet(self):
        if not self.packet_buffer.empty():
            return self.packet_buffer.get()
        return None
    
    def empty_packet_buffer(self):
        arr = []
        t = self.read_packet()
        while t:
            arr.append(t)
            t = self.read_packet()
        return arr


    