import numpy as np
import dacs
from scipy import optimize
from scipy.special import erf
#import stream
import api
from datetime import datetime

def noise_calc(pc=np.zeros(shape=(0,0,1), dtype='int'),
               noise=np.zeros(shape=(0,1), dtype='int'),
               noise_done=np.zeros(shape=(0,1), dtype='int'),
               thr_cnoise=np.zeros(shape=(0,1), dtype='int'),
               thr=0, thr_val=0, thr_noise=0):

      vals=np.argwhere(pc[thr]>thr_noise)
      for pix in vals:
          X=pix[0]
          Y=pix[1]
          if noise[X][Y]==0:
              noise[X][Y]=thr_val

      vals=np.argwhere(pc[thr]>5)
      for pix in vals:
          X=pix[0]
          Y=pix[1]
          if noise_done[X][Y]<2:
              noise_done[X][Y]=1

      vals=np.argwhere(noise>0)
      for pix in vals:
          X=pix[0]
          Y=pix[1]
          if pc[thr][X][Y]<=thr_noise and noise_done[X][Y]==1 :
              noise[X][Y]=noise[X][Y]-thr_val
              thr_cnoise[X][Y]=thr_val+noise[X][Y]/2.
              noise_done[X][Y]=2

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

#converts X,Y matrix (224,128) to Timepix4 internal SPGROUP address system
def addr_ColRow_to_EoCSpGroup(Col=0, Row=0):
    Top=(int)(Row/64)
    EoC=Col
    SpGroup=(int)(Row%64/16)
    Pix=Row%4
    if Top:
        SpGroup=SpGroup
        Pix=31-Pix
    else:
        SpGroup=15-SpGroup
        Pix=Pix
    return [-Top+1, EoC, SpGroup, Pix]

#converts Timepix4 internal address system to X,Y matrix
def addr_EoCSpPix_to_ColRow(addr=0):
    Pix=addr&0x1F
    Sp=(addr>>5)&0xF
    EoC=(addr>>9)&0xFF
    Top=(addr>>17)&0x1
    if Top:
         EoC = 223-EoC
         Sp=15-Sp
         Pix=31-Pix
    Col=2*EoC + (int)(Pix%8/4)
    Row=Pix%4 + (int)(Pix/8)*4 + Sp*16 + Top*256
    return [Col, Row]

def addr_EoCSpPix_to_ColRow_sinspect(top, eoc, pixnr):
    Pix=pixnr&0x1F
    Sp=(pixnr>>5)&0xF
    EoC=eoc
    Top=top
    if Top:
         EoC = 223-EoC
         Sp=15-Sp
         Pix=31-Pix
    Col=2*EoC + (int)(Pix%8/4)
    Row=Pix%4 + (int)(Pix/8)*4 + Sp*16 + Top*256
    return [Col, Row]


def errorf(x, *p):
    a, mu, sigma = p
    return 0.5*a*(1.0+erf((np.array(x)-mu)/(sigma*1.4142)))

def scurve_fit(x, a, b, c, d):
    return a / (1. + np.exp(-c * (x - d))) + b

def lin_fit(x,a, b):
    return a*x + b

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def tot(x,*p):
    a,b,c,t=p
    return (a*np.array(x)+b)-(c/(np.array(x)-t))

def tot_inv(tot, *p):
    a,b,c,t=p
    return (t*a+tot-b+pow(pow(b+t*a-tot,2)+4*a*c,0.5))/(2*a)

def linearize_DAC(DAC=0, OSR=1, STEPS=32,  service=0):
    x=[]
    y=[]
    print('Linearizing %s DAC'%DAC[3])
    DAC_VALUES = np.array(np.round(np.linspace(0, 2**DAC[4]-1, STEPS)), dtype=np.int)
    for dac_val in DAC_VALUES:
        ADC_int=dacs.Set_DAC(DAC=DAC, val=(0x4<<10)+dac_val, sampleADC=True, OSR=OSR, service=service, print_enable=False)
        x.append(dac_val)
        y.append(ADC_int)
    params, params_covariance = optimize.curve_fit(lin_fit, x, y)
    print(params)
    return params

def DAC_lin(DAC=0, target=0, params=0, service=0):
    dac_val=int((target - params[1])/params[0])
    if dac_val>=0 and dac_val<=2**DAC[4]-1:
        dacs.Set_DAC(DAC=DAC, val=(0x4<<10)+dac_val, sampleADC=False, OSR=0, service=service, print_enable=False)
        ret_val=dac_val*params[0] + params[1]
    else:
        ret_val=0
    return ret_val, dac_val

def linearize_TP(DAC_V=0, Gain_TP=25., OSR=1, STEPS=32,  service=0):
    x=[]
    y=[]
    print('Linearizing TP... ')
    vtpcoarse=dacs.Set_DAC(DAC=DAC_V[2], val=40, sampleADC=True, OSR=OSR, service=service, print_enable=False)
    DAC_VALUES = np.array(np.round(np.linspace(0, 2**DAC_V[6][4]-1, STEPS)), dtype=np.int)
    for dac_val in DAC_VALUES:
        vtp_fine=dacs.Set_DAC(DAC=DAC_V[6], val=(0x1<<10)+dac_val, sampleADC=True, OSR=OSR, service=service, print_enable=False)
        x.append(dac_val)
        y.append((vtp_fine-vtpcoarse)*Gain_TP)
        # print(vtp_fine, vtpcoarse,  y[-1])
    params, params_covariance = optimize.curve_fit(lin_fit, x, y)
    print(params)
    return params

def TP_energy(energy_ke=10., DAC_V=0, params=0, service=0):
    dac_val=int((energy_ke - params[1])/params[0])
    if dac_val>=0 and dac_val<=2**10-1:
        dacs.Set_DAC(DAC=DAC_V[6], val=(0x1<<10)+dac_val, sampleADC=False, OSR=0, service=service, print_enable=False)
        ret_val=dac_val*params[0] + params[1]
    else:
        ret_val=0
    return ret_val, dac_val

#def FB_readout(Queue=0, matrix=0, num_frames=0, printVal=False, service=0):
#    c_pack=0
#    top_bot='BOT','TOP'
#    segment_ON=False
#    packets_recieved_segment=0
#    Frame_done = False
#    Frame_num=0
#    fill_data=False
#    OP_MODE=0x1
#    GRAY_COUNTER=0
#    RATIO_VCO_CKDLL=0
#    NCHANNELS=0x0
#    top=0
#    segment_address=0
#    readout_mode_pkt=0
#
#    data_segment=[]
#
#    Second_frame_16B=False
#    Start_Frame=False
#    fill_data_done = False
#    segment_ON= False
#
#    ccc=0
#    if printVal:
#        filename1 = datetime.now().strftime("%Y%m%d-%H%M%S")
#        f=open('SCF'+filename1+'.txt','w')
#        print(filename1)
#    p_c=0
#    for tag, data in stream.queue_generator(Queue, 0.5):
#        #
#        pack=api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL)
#        if printVal:
#            if pack[0]=="CONTROL":
#                f.write("%6d\t%d\t%4d\t%16x\t%s\t%s\t%2x\n"%(p_c,segment_ON,c_pack,data,pack[0],top_bot[pack[1]],pack[2]))
#            else:
#                f.write("%6d\t%d\t%4d\t%16x\t%s\n"%(p_c,segment_ON,c_pack,data,pack[0]))
#        p_c+=1
#        if segment_ON:
#            if data==data_segment_end_pattern:
#                print(c_pack," %16x"%data_segment_end_pattern)
#            if c_pack < 1792:
#                data_segment.append([c_pack,data])
#                c_pack += 1
#            if c_pack == 1792:
#                fill_data_done=True
#                segment_ON = False
#                # print (data_segment[-1])
#                # print (api.decode_packet(data_segment[-1][1], OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL))
#        else:
#            pack=api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL)
#            # print (pack)
#            if pack[0] == 'CONTROL':# and not fill_data:
#                top=pack[1]
#                segment_ON=False
#                if pack[2] == 0xf0:
#                    ccc=0
#                    c_pack=0
#                    Frame_done = False
#                    Start_Frame = True
#                    # fill_data=False
#                    Second_frame_16B=False
#                    if printVal: print(' ############# START FRAME %s %d ###########'%(top_bot[top],Frame_num))
#                elif pack[2] == 0xf2 and Start_Frame:
#                    segment_ON=True
#                    segment_address=(pack[3]>>52) & 0x7
#                    readout_mode_pkt=(pack[3]>>50) & 0x3
#                    data_segment_end_pattern= data | 0x1 << 55
#                    # data_segment=np.zeros(shape=(1792), dtype='uint64')
#                    data_segment=[]
#                    fill_data_done = False
#                    # fill_data=True
#                    if printVal: print(' ############# START SEGMENT %s %d %d %d ###########'%(top_bot[top],Frame_num,segment_address, c_pack))
#                elif pack[2] == 0xf3 and fill_data_done:
#                    packets_recieved_segment=len(data_segment)#c_pack
#                    segment_address=(pack[3]>>52) & 0x7
#                    # segment_ON=False
#                    if printVal: print(' ############# STOP SEGMENT %s %d %d %d 16B: %d ccc %d ###########'%(top_bot[top],Frame_num,segment_address,c_pack,Second_frame_16B, ccc))
#                    c_pack=0
#                    frame_base_8B16B_1CH(top, readout_mode_pkt, data_segment, segment_address, Second_frame_16B, matrix, printVal=False)
#                    if segment_address == 7:
#                        Second_frame_16B=True
#                elif pack[2] == 0xf1:
#                    # c_pack=0
#                    Frame_done = True
#                    Start_Frame = False
#                    if printVal: print(' ############# FINISH FRAME %s %d ###########'%(top_bot[top],Frame_num))
#                    Frame_num += 1
#                    # segment_ON=False
#                    Second_frame_16B=False
#                else:
#                    ccc+=1
#            else:
#                ccc+=1
#
#        if Frame_done and Frame_num >= num_frames:
#            api.readout_control(Top=top, readout_enable=False, select_routing_table=0,nchannels=NCHANNELS, start_frame_readout=False,
#                                 read_packets_via_slow_ctrl=1, readout_mode=readout_mode_pkt, service=service )
#
#            if printVal:
#                print('############# READOUT STOPPED %s %d ###########'%(top_bot[top],Frame_num))
#            # break
#    if printVal:
#        f.close()
#    return packets_recieved_segment, Frame_num

#def FB_readout_noQ(topS=True, matrix=0, num_frames=0, printVal=False, service=0):
#    c_pack=0
#    top_bot='BOT','TOP'
#    addr=[0x4203,0xc203]
#    segment_ON=False
#    packets_recieved_segment=0
#    Frame_done = False
#    Frame_num=0
#    fill_data=False
#    OP_MODE=0x1
#    GRAY_COUNTER=0
#    RATIO_VCO_CKDLL=0
#    NCHANNELS=0x0
#    top=0
#    segment_address=0
#    readout_mode_pkt=0
#
#    data_segment=[]
#
#    Second_frame_16B=False
#    Start_Frame=False
#    fill_data_done = False
#    segment_ON= False
#
#    ccc=0
#    if printVal:
#        filename1 = datetime.now().strftime("%Y%m%d-%H%M%S")
#        f=open('SC_'+filename1+'.txt','w')
#        print(filename1)
#    p_c=0
#    finish=False
#    while(not finish):
#        dataP=rpc.decode_u256(service.ReadReg(rpc.ReadRegRequest(idx=0, addr=addr[topS], count=1)).data)
#        for data in dataP:
#            pack=api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL)
#            if printVal:
#                if pack[0]=="CONTROL":
#                    f.write("%6d\t%d\t%4d\t%16x\t%s\t%s\t%2x\n"%(p_c,segment_ON,c_pack,data,pack[0],top_bot[pack[1]],pack[2]))
#                else:
#                    f.write("%6d\t%d\t%4d\t%16x\t%s\n"%(p_c,segment_ON,c_pack,data,pack[0]))
#            p_c+=1
#            if segment_ON:
#                if data==data_segment_end_pattern:
#                    print(c_pack," %16x"%data_segment_end_pattern)
#                if c_pack < 1792:
#                    data_segment.append([c_pack,data])
#                    c_pack += 1
#                if c_pack == 1792:
#                    fill_data_done=True
#                    segment_ON = False
#                    # print (data_segment[-1])
#                    # print (api.decode_packet(data_segment[-1][1], OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL))
#            else:
#                pack=api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL)
#                # print (pack)
#                if pack[0] == 'CONTROL':# and not fill_data:
#                    top=pack[1]
#                    segment_ON=False
#                    if pack[2] == 0xf0:
#                        ccc=0
#                        c_pack=0
#                        Frame_done = False
#                        Start_Frame = True
#                        # fill_data=False
#                        Second_frame_16B=False
#                        if printVal: print(' ############# START FRAME %s %d ###########'%(top_bot[top],Frame_num))
#                    elif pack[2] == 0xf2 and Start_Frame:
#                        segment_ON=True
#                        segment_address=(pack[3]>>52) & 0x7
#                        readout_mode_pkt=(pack[3]>>50) & 0x3
#                        data_segment_end_pattern= data | 0x1 << 55
#                        # data_segment=np.zeros(shape=(1792), dtype='uint64')
#                        data_segment=[]
#                        fill_data_done = False
#                        # fill_data=True
#                        if printVal: print(' ############# START SEGMENT %s %d %d %d ###########'%(top_bot[top],Frame_num,segment_address, c_pack))
#                    elif pack[2] == 0xf3 and fill_data_done:
#                        packets_recieved_segment=len(data_segment)#c_pack
#                        segment_address=(pack[3]>>52) & 0x7
#                        # segment_ON=False
#                        if printVal: print(' ############# STOP SEGMENT %s %d %d %d 16B: %d ccc %d ###########'%(top_bot[top],Frame_num,segment_address,c_pack,Second_frame_16B, ccc))
#                        c_pack=0
#                        frame_base_8B16B_1CH(top, readout_mode_pkt, data_segment, segment_address, Second_frame_16B, matrix, printVal=False)
#                        if segment_address == 7:
#                            Second_frame_16B=True
#                    elif pack[2] == 0xf1:
#                        # c_pack=0
#                        Frame_done = True
#                        Start_Frame = False
#                        if printVal: print(' ############# FINISH FRAME %s %d ###########'%(top_bot[top],Frame_num))
#                        Frame_num += 1
#                        # segment_ON=False
#                        Second_frame_16B=False
#                    else:
#                        ccc+=1
#                else:
#                    ccc+=1
#
#            if Frame_done and Frame_num >= num_frames and not finish:
#                api.readout_control(Top=top, readout_enable=False, select_routing_table=0, nchannels=NCHANNELS, start_frame_readout=False,
#                                     read_packets_via_slow_ctrl=1, readout_mode=readout_mode_pkt, service=service )
#
#                if printVal: print('############# READOUT STOPPED %s %d ###########'%(top_bot[top],Frame_num))
#                finish=True
#                # break
#    if printVal:
#        f.close()
#    return packets_recieved_segment, Frame_num


def frame_base_8B16B_1CH(top=0, readout_mode_pkt=0x2, data=0, segment_address=0, Second_frame_16B=False, matrix=0, printVal=False):
    NUM_SEGS=28
    NUM_SP=64
    SEGS_SEP=4
    col_shift_base=(SEGS_SEP-segment_address)*2
    isL = -1
    if segment_address<4: #From L0-L3
        isL = 1

    for i in range(0,len(data)):
        block=int(data[i][0]/NUM_SEGS)
        col=data[i][0]%NUM_SEGS
        # if printVal and len(data)>0 :
        #     print (len(data), i, '%d\t'%data[i][0],'%16x'%data[i][1], block, col)
        col_shift= -col_shift_base - col*SEGS_SEP*2*isL
        if readout_mode_pkt==0x2:       # PC 8-bit
            for pix in [0,2,4,6]:
                val=(data[i][1]>>8*(7-pix)) & 0xFF
                X=224 + col_shift
                Y=int((pix/2)+block*4)
                if top:
                    X=447-X
                    Y=511-Y
                matrix[X][Y]+=val
                if (val !=0 and printVal): print(X, Y, val, '%16x'%data[i][1],col_shift, pix, col, block)
            for pix in [1,3,5,7]:
                val=(data[i][1]>>8*(7-pix)) & 0xFF
                X=224 + col_shift + 1
                Y=int((pix-1)/2+block*4)
                if top:
                    X=447-X
                    Y=511-Y
                matrix[X][Y]+=val
                if (val !=0 and printVal): print(X, Y, val, '%16x'%data[i][1], col_shift, pix, col, block )

        if readout_mode_pkt==0x3: #PC 16-bit
            pix_i=0
            for pix in [5,1,4,0]:
                val = ((data[i][1]>>8*pix) & 0xFF) + ((data[i][1]>>8*(pix+1)) & 0xFF00)
                X=224 + col_shift
                if Second_frame_16B:
                    X+=1
                Y=pix_i + block*4
                pix_i+=1
                if top:
                    X=447-X
                    Y=511-Y
                matrix[X][Y]+=val
                if (val !=0 and printVal): print(X, Y, val, '%16x'%data[i][1],col_shift, pix, col, block)

def find_packet(packet_info, cluster, CLUSTER_SIZE):
    SEARCH_LENGHT=100
    found=False
    cluster_num=0
    num_clusters=len(cluster)
    start_search=num_clusters - SEARCH_LENGHT
    if start_search < SEARCH_LENGHT :
        start_search=0

    for i in range(start_search,num_clusters,1):
        for j in range(0, len(cluster[i])):
            if abs(packet_info[0]-cluster[i][j][0]) < CLUSTER_SIZE and abs(packet_info[1]-cluster[i][j][1]) < CLUSTER_SIZE :
                if abs(packet_info[2]-cluster[i][j][2]) <= 2:
                    found=True
                    cluster_num=i
                    break
            else:
                break
        if found:
            break

    return found, cluster_num
