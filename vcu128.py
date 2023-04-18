import os
import sys
import socket
import time
import string
import _thread
import math


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

def SimpleWriteRequest(reg, val):
    if reg in dict:
        bites = dict[reg]/2
    elif 0x6100 <= reg <= 0x6eff or 0xE100 <= reg <= 0xEEFF:
        bites = 32
    elif 0x7000 <= reg <= 0x70DF or 0xF000 <= reg <= 0xF0DF:
        bites = 48
    elif 0x6000 <= reg <= 0x60DF or 0xE000 <= reg <= 0xE0DF:
        bites = 512
    else:
        bites = 2
    cmd_payload = bytearray(bites+10)
    cmd_payload[0] = 0x19
    cmd_payload[1] = 0xAA
    cmd_reg=val.to_bytes(bites,byteorder='big')
    for i,n in enumerate(cmd_reg):
        cmd_payload[4+i]=n
    sendit(cmd_payload, bites+10)
    
def writeTPX4(sock,payload,numbytes):
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


def packet_read_thread(q)
    global udp_data
    while True:
        udp_data, addr = sock.recvfrom(1024)
        udp_length = len(udp_data)
        if (udp_data[0]=0x77):          # packet data
            i = 1
            while (i < udp_length):
                word=int.from_bytes(udp_data[i:i+7],"big")
                q.append(word)
                i = i+8
        else:
            start = 0
            print('>raw{0}'.format(udp_data))
            while(start < udp_length):
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
def opensocket():
    try :
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.bind(("",UDP_CMD_PORT))
        return sock
    except socket.error as msg :
        print ('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()    

try:
    _thread.start_new_thread(listener_thread, ())
except:
    print("Error starting listening thread")
    quit()


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
