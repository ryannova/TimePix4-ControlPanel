import socket
import time
from signal import SIGINT, signal
import numpy as np
import base64

IP_ADDRESS = "localhost"
PORT = 7686

print("Sending timepix image packets to", IP_ADDRESS, "on port", PORT)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
header = np.zeros(16, dtype=np.int8)
image = np.ones(56*16*4*8, dtype=np.int16)
message = header.tobytes() + image.tobytes()
print("Packet length", len(message))

def handler(signal_recieved, frame):
    print('\nSIGINT or CTRL-C detected. Exiting')
    exit(0)

signal(SIGINT, handler)

while True:
    sock.sendto(message, (IP_ADDRESS, PORT))
    time.sleep(1)