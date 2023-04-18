import grpc
import rpc
import matplotlib.pyplot as plt
import numpy as np
import time
import xavi_config as ec
import api as api
import dacs as dacs
import struct
import sys
import matrix as mat
import random
# import read_packet_over_sc_with_fifo as pr
import queue
import stream
import conf_timepix4 as conf_tpix4
import equalize as eq
import shutil, os

if __name__ == '__main__':

    print(f"Arguments count: {len(sys.argv)}")
    fbase=False
    for i, arg in enumerate(sys.argv):
        # print(f"Argument {i:>6}: {arg}")
        if i==1:
            fbase = str(arg)

    EMPTY = rpc.Empty()
    with grpc.insecure_channel(ec.TIMEPIX_ADDRESS) as channel:

        # We'll assume Timepix 4 is located at index 0
        tpx4Service = rpc.Timepix4Stub(channel)
        peripheralService = rpc.PeripheralStub(channel)
        controlService = rpc.ControlInfoStub(channel)

        # Prepare the queue, and start the thread
        # This only needs to be done once.
        # q = queue.Queue()
        # pr.packet_read_thread(tpx4Service, q)

        TOT_TOA_MODE=0x0
        PC24b_MODE=0x3
        OP_MODE=PC24b_MODE
        GRAY_COUNTER=True
        BYPASS_CENTER=True
        TP_ON=False
        NUM_TP=300
        POLARITY=True
        LOW_GAIN=False
        LOG_GAIN=False
        SHUTTER_TIME_ON=0.000350
        SHUTTER_TIME_OFF=0.0001
        FBK_V=0.6
        THR_e=3000

        fbase_dacs='./CERN_scripts/common/'
        if not fbase:
            fbase='./results/W6_A5/'
            fbase='./results/W8_Si2/'
            fbase='./results/W8_Si1/'

        if not os.path.exists(fbase):
            os.makedirs(fbase)
            print("Created directory %s"%fbase)

        files = ['dacs_i.dat', 'dacs_v.dat']
        for f in files:
            shutil.copy(fbase_dacs + f, fbase)

        if BYPASS_CENTER:
            RATIO_VCO_CKDLL=21  #Should be 16 if VCO was ok
            T_CLK_DLL=16*1000/640
        else:
            RATIO_VCO_CKDLL=32  #Should be 16 if VCO was ok
            T_CLK_DLL=(16*1000/840)*2.

        DAC_I, DAC_VB, DAC_VT, AEOC, OSR = conf_tpix4.conf_timepix4(fbase=fbase_dacs,
                                                                GRAY_COUNTER=GRAY_COUNTER,
                                                                BYPASS_CENTER=BYPASS_CENTER,
                                                                POLARITY=POLARITY,
                                                                POWER_MODE=0,
                                                                LOW_GAIN=LOW_GAIN,
                                                                LOG_GAIN=LOG_GAIN,
                                                                NUM_TP=NUM_TP,
                                                                # PERIOD_TESTPULSE=200,
                                                                TP_ON=TP_ON,
                                                                OP_MODE=OP_MODE,
                                                                CHANNELS=0x00,
                                                                ENABLE_TOA=False,
                                                                ENABLE_TDC=False,
                                                                SHUTTER_TIME_ON=SHUTTER_TIME_ON,
                                                                SHUTTER_TIME_OFF=SHUTTER_TIME_OFF,
                                                                ENABLE_STATUS_PROC=True,
                                                                HEARTBEAT_ENABLE=False,
                                                                service=tpx4Service,
                                                                peripheral=peripheralService,
                                                                control=controlService)

        params_fbk,params_thr,ret_thr=conf_tpix4.conf_threshold(LOW_GAIN=LOW_GAIN,
                          THR_e=THR_e,
                          FBK_V=FBK_V,
                          POLARITY=POLARITY,
                          OSR=OSR,
                          DAC_VB=DAC_VB,
                          service=tpx4Service)

        q = queue.Queue()
        # pr.packet_read_thread(tpx4Service, q)
        stream.packet_read_thread(tpx4Service, q, top=True, bottom=True, forward_empty=True, tag=0)

        ARRAY_SIZE_X=448
        ARRAY_SIZE_Y=512
        NO_OF_PIXELS = 512 * 448

        # f=open('TP_full_col.txt','w')

        api.unmask_all_column_data(service=tpx4Service)
        # for n in range(120,224):
        #     api.column_data_mask(top=True, col=223-n, mask=True, service=tpx4Service)
        #
        # api.column_data_mask(top=True, col=223-3, mask=True, service=tpx4Service)

        RANGE_THR=400
        START=800
        THR_STEP=2

        t1=0
        pixelConfig = np.zeros(shape=(2,224,16,32), dtype=np.uint8)

        spacing=1
        for dac in range(0,32): #[0,15,16,31]: #range(0,32,31): #[0,15,31]: #range(246,267):#range(510,512,11):
            thr_scan = []
            thr_scan_mv = []
            pc=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
            thr_out= np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=float)
            noise=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
            noise_done=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
            thr_cnoise=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
            pileup=np.zeros(shape=(RANGE_THR,ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')

            for p_sp in range(0,spacing**2):

                for X in range(0,ARRAY_SIZE_X,1):
                    for Y in range(0,ARRAY_SIZE_Y,1):
                        addr=mat.addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
                        if X%spacing==p_sp%spacing and Y%spacing==int(p_sp/spacing):
                            pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=dac, power_enable=1, tp_enable=0, mask_bit=0)
                        else:
                            pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=random.randrange(32), power_enable=0, tp_enable=0, mask_bit=1)

                tpx4Service.ConfigPixels(rpc.Tpx4PixelConfig(idx = 0, config=pixelConfig.tobytes()))

                FROM_e=1000
                TO_e=-1000
                STEP_e=-25
                for thr in range(FROM_e,TO_e,STEP_e):

                    api.Datapath_Reset(service=tpx4Service)
                    params_fbk,params_thr,ret_thr=conf_tpix4.conf_threshold(LOW_GAIN=LOW_GAIN,
                                              THR_e=thr,
                                              FBK_V=FBK_V,
                                              POLARITY=POLARITY,
                                              LINEARIZE=False,
                                              PRINT_VAL=False,
                                              params_fbk=params_fbk,
                                              params_thr=params_thr,
                                              OSR=OSR,
                                              DAC_VB=DAC_VB,
                                              service=tpx4Service)

                # for thr in range(0,RANGE_THR):
                #     thr_val= (START - thr*THR_STEP)
                #     thr_scan.append(thr_val)
                #     adc=dacs.Set_DAC(DAC=DAC_VB[5], val=(0x4<<10)+thr_val , sampleADC=True, OSR=OSR, service=tpx4Service, print_enable=False)    #VThr
                    # thr_scan_mv.append(adc*1000.)

                    api.Shutter_open(service=tpx4Service)
                    c_pack=0
                    pix_counter=0
                    pileup_c=0
                    shutter_time=0

                    # Reads top+bottom Periphery through SC
                    enable_exit=[0,0]

                    t1=[0,0]
                    # RATIO_VCO_CKDLL=float(thr_val/1000.)
                    while enable_exit[0]==0 or enable_exit[1]==0:
                        for data in stream.queue_generator(q, 0.2):
                            # print (c_pack, data, api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL))
                            pack=api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL)
                            # print("here")

                            Top=pack[1]
                            # print (c_pack,api.decode_packet(data),sys.stdout.flush())
                            addr=mat.addr_EoCSpPix_to_ColRow(addr=pack[2])
                            if pack[0] == 'DATA PC24b':
                                # print (c_pack,addr,pack, pack[2])
                                pc[addr[0]][addr[1]] +=  pack[3]
                                if noise_done[addr[0]][addr[1]] == 0 :
                                    thr_out[addr[0]][addr[1]] = thr
                                    noise_done[addr[0]][addr[1]] = 1
                                c_pack+=1
                            if pack[0] == 'CONTROL':
                                if pack[2] == 225:  #Shutter rise
                                    if Top:
                                        t1[1] = pack[3]
                                    else:
                                        t1[0] = pack[3]
                                if pack[2] == 226 and (t1[0]>0 or t1[1]>0):
                                    if Top:
                                        enable_exit[1]=1   #Shutter fall
                                        shutter_time=(pack[3]-t1[1])*0.025
                                    else:
                                        enable_exit[0]=1   #Shutter fall
                                        shutter_time=(pack[3]-t1[0])*0.025

                    masked=0

                    if OP_MODE == PC24b_MODE:
                        api.reset_matrix(reset_pixel_conf=False, service=tpx4Service)
                        num_active_pixels_thr=len(np.argwhere(noise_done==2))
                        num_noise_done_pixels=num_active_pixels_thr

                        vals=np.argwhere(noise_done==1)
                        masked=len(vals)
                        for i in vals:
                            X=i[0]
                            Y=i[1]
                            addr=mat.addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
                            pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=31, power_enable=1, tp_enable=0, mask_bit=1)
                            noise_done[X][Y]=2
                        if masked:
                            tpx4Service.ConfigPixels(rpc.Tpx4PixelConfig(idx = 0, config=pixelConfig.tobytes()))

                    print ('Dac:%3d\t%3d\t Thr:%3d\t %5d\t Shutter:%.2fus\t DataPacketsRecieved:%4d\t ActivePixels:%4d Done:%4d Masked:%4d'
                           %(dac,p_sp, thr, ret_thr, shutter_time,c_pack, num_active_pixels_thr, num_noise_done_pixels, masked))   #clk_40_sp is at 5MHz

            # Save Results of scans
            vals=[]

            if OP_MODE == PC24b_MODE:
                # np.savetxt('noise_out2.csv', noise_out, delimiter='\t', fmt='%.2f')
                np.savetxt(fbase+'//dac_%d.csv'%dac, np.where(noise_done==2,thr_out,-10000), delimiter='\t', fmt='%d')
                stdv=np.std(thr_out[noise_done==2])
                avr=np.average(thr_out[noise_done==2])
                print('dac: %d mean %.2f stdev %.2f'%(dac,avr,stdv))
                plt.figure(figsize = (10,10))
                plt.imshow(np.flip(np.rot90(thr_out),0), origin='lower', vmin=avr-4*stdv, vmax=avr+4*stdv)
                plt.colorbar()

                # plt.savefig(fbase+"dac_%d.png"%dac)
                plt.title("dacacode:%d mean:%.2f stdev:%.2f" %(dac,avr,stdv))
                plt.ylabel("Rows")
                plt.xlabel("Columns")
                plt.savefig(fbase+"//dac_%d.png"%dac, dpi=500)
                # plt.show(block=False)
                # plt.show()
                # plt.pause(0.001)

        api.set_dll_clk(lock_threshold=1, toa_clk_edge=0, enable_toa=False, toa_bin_or_gray=True, bypass_center_pll=True, enable_cols=False, service=tpx4Service)
        api.readout_control(Top=True, readout_enable=0, service=tpx4Service)
        api.readout_control(Top=False, readout_enable=0, service=tpx4Service)
        np.savetxt(fbase+'//DAC_thr.csv', thr_scan_mv, delimiter='\t', fmt='%.2f')

        eq.eq_broute_force(fbase,0,32,1)
