import numpy as np

#converts X,Y matrix (448,512) to Timepix4 internal PIXEL address system
def addr_ColRow_to_EoCSpPix(Col=0, Row=0):
    EoC=(int)(Col/2)
    Sp=(int)(Row%256/16)
    Pix=Row%4 +(int)(Row%16/4)*8 +(Col%2)*4
    Top=(int)(Row/256)
    if Top:
        Sp=Sp
        Pix=31-Pix
    else:
        Sp=15-Sp
        Pix=Pix
    return [-Top+1, EoC, Sp, Pix]

def pixel_conf(dac_bits=0x0, power_enable=1, tp_enable=0, mask_bit=0):
    conf = dac_bits & 0x1F
    conf |= power_enable<<5 &0x20
    conf |= tp_enable<<6 &0x40
    conf |= mask_bit<<7 &0x80
    return conf

def SimpleWritePlaceHolder(addr: bytes =0x000, data : np.ndarray =np.zeros(shape=(32*16,1), dtype=np.uint8)):
    print("Wrote {} bytes to address {}".format(data.size, hex(addr)))


def PixelConfig(Top=True, EoC=0x0, SpGroup=0, data=np.zeros(shape=(32*16,1), dtype=np.uint8), service=0):
    if Top:
        SimpleWritePlaceHolder(addr=0xe000 + EoC, data=data)
        #service.SimpleWrite(rpc.SimpleWriteRequest(addr=0xe000 + EoC, data=data, count=1))
    else:
        SimpleWritePlaceHolder(addr=0x6000 + EoC, data=data)
        #service.SimpleWrite(rpc.SimpleWriteRequest(addr=0x6000 + EoC, data=data, count=1))

ARRAY_SIZE_X=448
ARRAY_SIZE_Y=512
equal=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=np.uint8)
pixelConfig = np.zeros(shape=(2,224,16,32), dtype=np.uint8)
mask=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=np.uint8)

for X in range(0,ARRAY_SIZE_X,1):
    for Y in range(0,ARRAY_SIZE_Y,1):
        addr=addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
        # if Y<9 or Y>(511-9) or (Y>(255-7) and Y<(256+6)) or (X>=221 and X<=227) or X==0 or X==447: # or X==0:
        #     pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=equal[X][Y], power_enable=not(mask[X][Y]), tp_enable=0, mask_bit=1)
        # else:
        pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=pixel_conf(dac_bits=equal[X][Y], power_enable=not(mask[X][Y]), tp_enable=0, mask_bit=mask[X][Y])

#tpx4Service.ConfigPixels(rpc.Tpx4PixelConfig(idx = 0, config=pixelConfig.tobytes()))


def ConfigPixels(pixelConfigBytes : bytes):
    step = 512
    EoC_counter = 0x0
    for i in range(0, len(pixelConfigBytes)//2, step):
        PixelConfig(Top=True, EoC=EoC_counter, data=np.frombuffer(pixelConfigBytes[i:i+step], dtype=np.uint8))
        EoC_counter += 1
    
    EoC_counter = 0x0
    for i in range(len(pixelConfigBytes)//2, len(pixelConfigBytes), step):
        PixelConfig(Top=False, EoC=EoC_counter, data=np.frombuffer(pixelConfigBytes[i:i+step], dtype=np.uint8))
        EoC_counter += 1
    
ConfigPixels(pixelConfig.tobytes())

