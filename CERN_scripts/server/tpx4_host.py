import os
import sys
import socket
import time
import string
import _thread
import math

debug_print = 0

#Send to hard-coded VCU128 address
UDP_SRC_IP = "192.168.1.100"
UDP_DEST_IP = "192.168.1.10"
#VCU128 expects commands on this port
UDP_CMD_PORT= 5001

data = ''       # storage for incoming packets

dict = {0x9000:8,
        0xA01A:8,
        0xA020:8,
        0xA034:8,
        0x4202:8,
        0x4207:8,
        0x4208:8,
        0x4209:8,
        0x4300:8,
        0x4B02:8,
        0x4C07:8,
        0x4D21:8,
        0x4B00:8,
        0x4B01:8,
        0x4B03:8,
        0x4B04:8,
        0x4B05:8,
        0x4B06:8,
        0x4B07:8,
        0x4B08:8,
        0xC202:8,
        0xC207:8,
        0xC208:8,
        0xC209:8,
        0xC300:8,
        0xCB02:8,
        0xCC07:8,
        0xCD21:8,
        0xCB00:8,
        0xCB01:8,
        0xCB03:8,
        0xCB04:8,
        0xCB05:8,
        0xCB06:8,
        0xCB07:8,
        0xCB08:8,
        0xAFFF:32,
        0x4203:32,
        tuple(range(0x6100,0x6eff)):32,
        tuple(range(0xE100,0xEeff)):32,
        0xAFFE:48,
        tuple(range(0x7000,0x70DF)):48,
        tuple(range(0xF000,0xF0DF)):48,
        tuple(range(0x6000,0x60df)):512,
        tuple(range(0xE000,0xE0df)):512
}

def sendit(payload,numbytes):
    print('Sending %d bytes\n' % numbytes)
    if (numbytes > 1500):
        for x in range(math.ceil(numbytes/1500 + 1)):
            if ((x+1)*1500) > numbytes:
                end = numbytes
            else:
                end = (x+1)*1500
            sock.sendto(bytes(payload[x*1500:end]), (UDP_DEST_IP, UDP_CMD_PORT))
            time.sleep(.015)
    else:
        sock.sendto(bytes(payload[:numbytes]), (UDP_DEST_IP, UDP_CMD_PORT))
    time.sleep(.005)
    if debug_print: print (payload)


def listener_thread():
    global udp_data
    while True:
        udp_data, addr = sock.recvfrom(1024)
        start = 0
        print('>raw{0}'.format(udp_data))
        while(start < len(udp_data)):
            sync = udp_data.decode().find('AA',start)
            if (sync == -1):
                break
            #print('sync %d\n' % sync)
            rw = int(udp_data[sync+2:sync+6].decode(),16)
            reg = int(udp_data[sync+8:sync+12].decode(),16)
            #print('reg %x\n' % reg)
            stat = udp_data[sync+12:sync+14]
            #print('stat %s\n' % stat)
            if reg in dict:
                nibbles = dict[reg]
            elif 0x6100 <= reg <= 0x6eff or 0xE100 <= reg <= 0xEEFF:
                nibbles = 64
            elif 0x7000 <= reg <= 0x70DF or 0xF000 <= reg <= 0xF0DF:
                nibbles = 96
            elif 0x6000 <= reg <= 0x60DF or 0xE000 <= reg <= 0xE0DF:
                nibbles = 1024
            else:
                nibbles = 4
            #print('Expecting %d nibbles\n' % nibbles)
            if (rw == 1):
                payload = udp_data[sync+14:sync+14+nibbles]
                start = sync+14+nibbles
                print('>Register %x: Status %s: Payload %s\n' % (reg, stat, payload))
            else:
                start = sync+14
                print('>Register %x: Status %s:\n' % (reg, stat))


print (" **********UDP to VCU128 Test ***************")
try :
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.bind(("",UDP_CMD_PORT))
except socket.error as msg :
    print ('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()    
#    sock.connect("localhost",UDP_CMD_PORT)

try:
    _thread.start_new_thread(listener_thread, ())
except:
    print("Error starting listening thread")
    quit()

while True:
    inp = input('''Enter
    "Wreg" to write reg to Timepix,
    "Rreg" to read reg from Timepix,
    "TR" to reset Timepix,
    "GO" to remove reset from Timepix,
    "T1" to read from temperature sensor 1,
    "T2" to read from temperature sensor 2,
    "T3" to read from temperature sensor 3,
    "T4" to read from temperature sensor 4,
    "FI" to read commands from a file,
    "RI" to read I2C MUX,
    "I2" to write I2C MUX
    or "q" to quit\n\r''')
    inp = inp.upper()
    if inp == 'Q':
        quit()
    elif inp[0] == 'W':
        cmd_payload = bytearray(16)
        cmd_payload[0] = 0x19
        cmd_payload[1] = 0xAA
        cmd_reg=bytearray.fromhex(inp[1:])
        for i,n in enumerate(cmd_reg):
            cmd_payload[4+i]=n
        sendit(cmd_payload, 16)
    elif inp[0] == 'R':
        cmd_payload = bytearray(16)
        cmd_payload[0] = 0x19
        cmd_payload[1] = 0xAA
        cmd_payload[3] = 0x1
        cmd_reg=bytearray.fromhex(inp[1:])
        for i,n in enumerate(cmd_reg):
            cmd_payload[4+i]=n
#        cmd_payload[4] = (reg >> 8) & 0xff
#        cmd_payload[5] = reg & 0xff
        sendit(cmd_payload, 16)
    elif inp == 'TR':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x05
        sendit(cmd_payload, 8)
    elif inp == 'GO':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x03
        sendit(cmd_payload, 8)
    elif inp == 'T1':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x20
        sendit(cmd_payload, 8)
    elif inp == 'T2':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x21
        sendit(cmd_payload, 8)
    elif inp == 'T3':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x22
        sendit(cmd_payload, 8)
    elif inp == 'T4':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x23
        sendit(cmd_payload, 8)
    elif inp == 'FI':
        fname = input("Enter file name:")
        if (fname!=""):
            f = open(fname,"r")
            cmd_payload = bytearray(10000)
            cmd_payload[0] = 0x19
            flen = 1
            while(True):
                line=f.readline().strip().replace(" ","")
                print(line)
                if not line:
                    break
                i=1
                k=3
                cmd_payload[flen] = 0xAA
                cmd_payload[flen+1] = 0
                if line[0]=='R' or line[0]=='r':
                    cmd_payload[flen+2] = 1
                    while(i<len(line)):
                        cmd_payload[flen+k] = int(line[i:i+2],16)
                        #print("%s:%2x" % (line[i:i+2], int(line[i:i+2],16)))
                        i += 2
                        k += 1
                    flen += (len(line[1:])>>1) + 13 
                    #flen += (len(line[1:])>>1) + 43
                elif line[0]=='W' or line[0]=='w':
                    cmd_payload[flen+2] = 0
                    while(i<len(line)):
                        cmd_payload[flen+k] = int(line[i:i+2],16)
                        #print("%s:%2x" % (line[i:i+2], int(line[i:i+2],16)))
                        i += 2
                        k += 1
                    flen += (len(line[1:])>>1) + 13
                    #flen += (len(line[1:])>>1) + 43
                #print ('flen %d' % flen)
            cmd_payload[flen+k] = 0;      # fill packet with extra 0s to ensure command fills 32 bits
            cmd_payload[flen+k+1] = 0;
            cmd_payload[flen+k+2] = 0;
            #for n in range(24):
            #   print(hex(cmd_payload[n]))
            #print(cmd_payload)
            sendit(cmd_payload,flen)
    elif inp == 'RI':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x24
        sendit(cmd_payload, 8)
    elif inp == 'I2':
        cmd_payload = bytearray(8)
        cmd_payload[0] = 0x25
        sendit(cmd_payload, 8)


#   sock.sendto(bytes(payload),(UDP_DEST_IP,UDP_CMD_PORT))
#    dataAddr = sock.recvfrom(2000)
#    address = dataAddr[1]
#    msg = "Message from :{}".format(address)
#    print(msg)
    time.sleep(1)

def parseudp(udp_data):
    start = 0
    print('>raw{0}'.format(udp_data))
    while(start < len(udp_data)):
        sync = udp_data.decode().find('AA',start)
        if (sync == -1):
            break
        #print('sync %d\n' % sync)
        reg = int(udp_data[sync+8:sync+12].decode(),16)
        #print('reg %x\n' % reg)
        stat = udp_data[sync+12:sync+13]
        #print('stat %s\n' % stat)
        if reg in dict:
            nibbles = dict[reg]
        elif 0x6100 <= reg <= 0x6eff or 0xE100 <= reg <= 0xEEFF:
            nibbles = 64
        elif 0x7000 <= reg <= 0x70DF or 0xF000 <= reg <= 0xF0DF:
            nibbles = 96
        elif 0x6000 <= reg <= 0x60DF or 0xE000 <= reg <= 0xE0DF:
            nibbles = 1024
        else:
            nibbles = 4
        #print('Expecting %d nibbles\n' % nibbles)
        payload = udp_data[sync+14:sync+14+nibbles]
        start = sync+15+nibbles
        print('>Register %x: Status %s: Payload %s\n' % (reg, stat, payload))
