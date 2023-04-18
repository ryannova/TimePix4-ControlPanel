import sys
sys.path.insert(1,'./common')
import matplotlib.pyplot as plt
import numpy as np
import math
import time
import api as api
import dacs as dacs
import struct
import matrix as mat
import random
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.colors as colors
from matplotlib.ticker import MultipleLocator
import matplotlib.colors as colors
#import stream
import queue
from scipy import optimize
import conf_timepix4 as conf_tpix4



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

        TOT_TOA_MODE=0x0
        PC24b_MODE=0x3
        OP_MODE=TOT_TOA_MODE
        THR_EQUALIZED=True
        GRAY_COUNTER=True
        BYPASS_CENTER=True
        MASKED=True
        NOISE_MASK1=False
        DETECT_NOISY_PIXELS=False
        THRESHOLD_NOISY_PIXEL=5
        SHIFT_EQCODE_NOISY_PIXELS=False
        EQCODE_MASK1=True
        TP_ON=False
        POLARITY=True
        LOW_GAIN=False
        LOG_GAIN=False

        NUM_TP=1
        Gain_TP=20.
        FBK_V=0.7
        # THR_FBK_V=0.02
        THR_e=800

        SHUTTER_TIME_ON=1
        SHUTTER_TIME_OFF=0.001
        CLUSTER_SIZE_ACCEPTANCE_MIN=1
        CLUSTER_SIZE_ACCEPTANCE_MAX=100
        CLUSTER_SIZE=20
        MAX_keV=75
        SORT_BY_MAX_TOT=False

        if not fbase:
            fbase='./results/W6_A5/'
            fbase='./results/W8_Si2/'
            fbase='./results/W8_Si1/'

        if BYPASS_CENTER:
            RATIO_VCO_CKDLL=20.3  #Should be 16 if VCO was ok
            RATIO_VCO_CKDLL=21.5  #Should be 16 if VCO was ok
            T_CLK_DLL=16*1000/640
        else:
            RATIO_VCO_CKDLL=32  #Should be 16 if VCO was ok
            T_CLK_DLL=(16*1000/840)*2.


        DAC_I, DAC_VB, DAC_VT, AEOC, OSR = conf_tpix4.conf_timepix4(fbase=fbase,
                                                                GRAY_COUNTER=GRAY_COUNTER,
                                                                BYPASS_CENTER=BYPASS_CENTER,
                                                                POLARITY=POLARITY,
                                                                LOW_GAIN=LOW_GAIN,
                                                                LOG_GAIN=LOG_GAIN,
                                                                NUM_TP=NUM_TP,
                                                                TP_ON=TP_ON,
                                                                POWER_MODE=0,
                                                                CHANNELS=0x00,
                                                                OP_MODE=OP_MODE,
                                                                TP_DIGITAL=True,
                                                                SHUTTER_TIME_ON=SHUTTER_TIME_ON,
                                                                SHUTTER_TIME_OFF=SHUTTER_TIME_OFF,
                                                                service=tpx4Service,
                                                                peripheral=peripheralService,
                                                                control=controlService)

        q = queue.Queue()
        stream.packet_read_thread(tpx4Service, q, top=True, bottom=True, forward_empty=False, tag=0)

        ARRAY_SIZE_X=448
        ARRAY_SIZE_Y=512
        NO_OF_PIXELS = 512 * 448

        if THR_EQUALIZED:
            equal=np.loadtxt(fbase + 'eq_codes.dat', dtype=np.uint8)
            if EQCODE_MASK1:
                try:
                    equal=np.loadtxt(fbase + 'equal_equal_1.dat', dtype=np.uint8)
                except:
                    equal=np.loadtxt(fbase + 'eq_codes.dat', dtype=np.uint8)
        else:
            equal=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=np.uint8)

        if MASKED:
            mask=np.loadtxt(fbase + 'eq_mask.dat', dtype=np.uint8)
            if NOISE_MASK1:
                try:
                    mask=np.loadtxt(fbase + 'mask_equal_1.dat', dtype=np.uint8)
                except:
                    mask=np.loadtxt(fbase + 'eq_mask.dat', dtype=np.uint8)
        else:
            mask=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=np.uint8)

        conf_tpix4.conf_threshold(LOW_GAIN=LOW_GAIN,
                                  THR_e=THR_e,
                                  FBK_V=FBK_V,
                                  OSR=OSR,
                                  DAC_VB=DAC_VB,
                                  service=tpx4Service)

        RANGE_THR=1
        START=500
        STOP=10500
        THR_STEP=int((STOP-START)/RANGE_THR)

        thr_out= np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=float)
        noise_out = np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype=float)
        t1=0
        pixelConfig = np.zeros(shape=(2,224,16,32), dtype=np.uint8)
        max_ftoa_rise=0
        max_ftoa_fall=0
        pc=np.zeros(shape=(RANGE_THR,ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        tot_ok=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        noise_done=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        tot_mean=np.zeros(shape=(RANGE_THR,ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='float')
        tot_stdev=np.zeros(shape=(RANGE_THR,ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='float')
        thr_cnoise=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        pileup=np.zeros(shape=(RANGE_THR,ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        tot_m=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='float')
        toa_m=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='float')
        toa_ref0=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='float')
        pc_m=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        tot_map=np.zeros(shape=(30,30), dtype='float')
        toa_map=np.zeros(shape=(30,30), dtype='float')
        pc_map=np.zeros(shape=(30,30), dtype='int')
        toa_neg_map=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')

        for X in range(0,ARRAY_SIZE_X,1):
            for Y in range(0,ARRAY_SIZE_Y,1):
                toa_ref0[X][Y]=-1
        ftoa_fall_hist=[]
        ftoa_rise_hist=[]
        uftoa_start_hist=[]

        uftoa_stop_hist=[]
        toa_hist=[]
        tot_hist=[]
        tot_hist_clusters={}
        for i in range(CLUSTER_SIZE_ACCEPTANCE_MIN,CLUSTER_SIZE_ACCEPTANCE_MAX):
            tot_hist_clusters[i]=[]
        tot_hist_clusters_size=[]
        thr_val_a=[]

        ctpr_eoc= np.zeros(shape=(2,224), dtype=int)
        print('Setting PixelConfig')

        for X in range(0,ARRAY_SIZE_X,1):
            for Y in range(0,ARRAY_SIZE_Y,1):
                addr=mat.addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
                # if Y<9 or Y>(511-9) or (Y>(255-7) and Y<(256+6)) or (X>=221 and X<=227) or X==0 or X==447: # or X==0:
                #     pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=equal[X][Y], power_enable=not(mask[X][Y]), tp_enable=0, mask_bit=1)
                # else:
                pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=equal[X][Y], power_enable=not(mask[X][Y]), tp_enable=0, mask_bit=mask[X][Y])

        tpx4Service.ConfigPixels(rpc.Tpx4PixelConfig(idx = 0, config=pixelConfig.tobytes()))


        c_pack=0
        pix_counter=0
        pileup_c=0
        shutter_time=0

        # Reads bottom Periphery
        enable_exit=[0,0]
        empty_data=0
        t1=[0,0]
        th=[0,0]
        heartbit_num=[0,0]
        tot_hd=[]
        cluster=[]

        t0=0
        dac_s=0
        tot_short_c=0

        mask_sp=0x03FF_FFFF_FFFF_FFFF
        mask_sp=0x0200_0000_0000_0000
        mask_sp=0x0000_0000_0000_0000
        SPColConfig = np.zeros(3*16, dtype=np.uint8)

        for n in range(0,len(SPColConfig),3):
            if mask_sp >> int(n*(4/3)) + 0 & 0x1:
                SPColConfig[n+2] = 0x1
            if mask_sp >> int(n*(4/3)) + 1 & 0x1:
                SPColConfig[n+2] |= 0x40
            if mask_sp >> int(n*(4/3)) + 2 & 0x1:
                SPColConfig[n+1] = 0x10
            if mask_sp >> int(n*(4/3)) + 3 & 0x1:
                SPColConfig[n] |= 0x4

        # for i in range(0,len(SPColConfig)):
        #     print('%d %x'%(i,SPColConfig[i]))
        # print(SPColConfig.tobytes())
        # api.write_spgroup(top=True, dcol=0,val=SPColConfig.tobytes(), service=tpx4Service)
        # tpx4Service.WriteReg(rpc.WriteRegRequest(idx=0, addr=0xf000+20, data=SPColConfig.tobytes(), count=1))
        tpx4Service.WriteReg(rpc.WriteRegRequest(idx=0, addr=0x7000+int(343/2), data=SPColConfig.tobytes(), count=1))
        f=open(fbase +  'clustersP_%de_%3.2fs.txt'%(THR_e,SHUTTER_TIME_ON),'w')
        api.T0_sync(service=tpx4Service)
        api.Shutter_open(service=tpx4Service)
        # RATIO_VCO_CKDLL=float(thr_val/1000.)
        while enable_exit[0]==0 or enable_exit[1]==0:
            # print(enable_exit)
            for data in stream.queue_generator(q, 0.0001):
                # print (c_pack, data, api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL))
                pack=api.decode_packet(data, OP_MODE, GRAY_COUNTER, RATIO_VCO_CKDLL)

                Top=pack[1]
                # print (c_pack,pack)
                addr=mat.addr_EoCSpPix_to_ColRow(addr=pack[2])
                X=addr[0]
                Y=addr[1]
                if pack[0] == 'DATA TOA-TOT': # and pack[11]<2047 and pack[11]>0: #TOT=2047 remove noise packets
                    # print (c_pack,X,Y,pack[16],pack[14],th[Top]-t1[Top], th[Top], t1[Top], heartbit_num)
                    ftoa_rise=pack[9]
                    ftoa_fall=pack[10]
                    tot_hd=pack[14]*T_CLK_DLL
                    # tot_hd_e=mat.tot_inv(tot_hd, *[a_tot[X][Y],b_tot[X][Y],c_tot[X][Y],t_tot[X][Y]])
                    # tot_hd_eV=tot_hd_e*0.00362
                    pack_time=(th[Top]-t1[Top])*T_CLK_DLL*10**-9
                    packet_info=[X,Y, pack[16], tot_hd, pack_time ,c_pack, pack[6], pack[7], pack[8], ftoa_rise, ftoa_fall, pack[11], pack[17], pack[12]]
                    f.write("%2d\t%3d\t%3d\t%6.4f\t%6.6f\t"%(c_pack,X,Y,pack_time,tot_hd))
                    f.write("%6d\t%3d\t%3d\t%3d\t%3d\t%3d\t%3d\t"%(packet_info[6],packet_info[7],packet_info[8],packet_info[9],packet_info[10],packet_info[11],packet_info[12]))
                    f.write("(%1d)\n"%(packet_info[13]))
                    f.flush()
                    # if not math.isnan(tot_hd_eV):
                    #     packet_info=[X,Y, pack[16], tot_hd, th[Top]-t1[Top],c_pack,pack[6], pack[7], pack[8], ftoa_rise, ftoa_fall, pack[11], pack[17], pack[12]]
                    # else:
                    #     packet_info=[X,Y, pack[16], 0., th[Top]-t1[Top],c_pack,pack[6], pack[7], pack[8], ftoa_rise, ftoa_fall, pack[11], pack[17], pack[12]]
                    # packet_info=[X,Y, pack[6]-pack[9]/RATIO_VCO_CKDLL, pack[14],th[Top]-t1[Top],c_pack]
                    print(packet_info)
                    found, cluster_num = mat.find_packet(packet_info, cluster, CLUSTER_SIZE)
                    if not found:
                        cluster.append([])
                        cluster_num=len(cluster)-1
                        # print (found,cluster_num,len(cluster[cluster_num]),X,Y,pack[16],pack[14],th[Top]-t1[Top], th[Top], t1[Top], heartbit_num)
                        # print (found, cluster_num)
                    if pack[11] > 0:
                        cluster[cluster_num].append(packet_info)
                    # else:
                    #     tot_short_c += 1
                    #     toa_neg_map[X][Y]+=1
                    # print (found,cluster_num,len(cluster[cluster_num]),X,Y,pack[16],pack[14],tot_hd_e)
                    # if pack[9] > 20:
                    # if c_pack==0:
                    #     t0=pack[16]
                    # time_corrected = pack[16]-(int(c_pack/num_active_pixels)*PERIOD_TESTPULSE*2)%(2**16)
                    # if time_corrected <0:
                    #     time_corrected = time_corrected + 2**16
                    # time_corrected -=t0
                     # print (c_pack, X,Y, pack[4],  pack[6], pack[7], pack[8], pack[9], pack[10], pack[11], pack[13],pack[14],pack[15],pack[16], time_corrected  )

                    # tot_hist.append(tot_hd)
                    # tot_hd=pack[13]*T_CLK_DLL
                    # tot_hd=time_corrected*T_CLK_DLL
                    tot_m[X][Y]=tot_hd
                    toa_m[X][Y]=pack[16]*25.
                    pc_m[X][Y]+=1

                    c_pack+=1

                if pack[0] == 'CONTROL':
                    # print (c_pack,addr,pack, pack[2])
                    if pack[2] == 224:  #Heartbit
                        # print (c_pack,addr,pack, pack[2])
                        th[Top]=pack[3]
                        heartbit_num[Top] += 1
                        # if Top and t1[1]>0:
                        #     print ('Time: %.6fs'%((pack[3]-t1[1])*25*8*10**-9))
                        # if not Top and t1[0]>0:
                        #     print ('Time: %.6fs'%((pack[3]-t1[0])*25*8*10**-9))
                    if pack[2] == 225:  #Shutter rise
                        print (c_pack,addr,pack, pack[2])
                        t1[Top] = pack[3]

                    if pack[2] == 226 and (t1[0]>0 or t1[1]>0):
                        enable_exit[Top]=1   #Shutter fall
                        shutter_time=(pack[3]-t1[Top])*0.025*8  #Should be 16 if VCO was ok*8
                        print (addr,pack, pack[2],enable_exit)
        print("Finished!")
        f.close()

        alphas=0
        alphas_pos_timing=0
        f=open(fbase +  'clusters_%de_%3.2fs.txt'%(THR_e,SHUTTER_TIME_ON),'w')

        def sortTOT(val):
            return val[3]
        def sort2(val):
            return val[2]

        data_TOT_TOA=[]
        data_TOT_TOA.append([1,-20])
        data_TOT_TOA.append([1,30])

        ftoa_fall_hist=[]
        ftoa_rise_hist=[]
        uftoa_start_hist=[]
        uftoa_stop_hist=[]

        for i in range(len(cluster)):
            max_tot=0
            toa_at_max_tot=2**16
            X=0
            Y=0
            tot_cluster=0
            for j in range(len(cluster[i])):
                # print(i,cluster[i][j]) #,max(cluster[i][0]),max(cluster[i][1]),max(cluster[i][3]))
                tot_cluster+=cluster[i][j][3]
                #Sort by max TOT
                if cluster[i][j][3]>=max_tot and SORT_BY_MAX_TOT:
                    max_tot=cluster[i][j][3]
                    toa_at_max_tot=cluster[i][j][2]
                    X=cluster[i][j][0]
                    Y=cluster[i][j][1]
                #Sort by min TOA
                if cluster[i][j][2]<=toa_at_max_tot and not SORT_BY_MAX_TOT:
                    max_tot=cluster[i][j][3]
                    toa_at_max_tot=cluster[i][j][2]
                    X=cluster[i][j][0]
                    Y=cluster[i][j][1]

            # print (max_tot, X, Y)
            # tot_hist_clusters.append(tot_cluster)
            tot_hist_clusters_size.append(len(cluster[i]))

            cluster_size=len(cluster[i])

            if cluster_size >= CLUSTER_SIZE_ACCEPTANCE_MIN and cluster_size < CLUSTER_SIZE_ACCEPTANCE_MAX : #and max_tot<2000:
                alphas+=1
                tot_hist_clusters[cluster_size].append(tot_cluster)
                f.write('Cluster# %d (%d)\t%3d\t%3d\t%.6f\t%.2f\t%.2f\n'%(i, cluster_size, X, Y,toa_at_max_tot,max_tot,tot_cluster))
                cluster[i].sort(key=sortTOT)
                cluster_sorted=cluster[i]
                # print (cluster[i])
                neg_timing=False
                for j in range(len(cluster_sorted)):
                    # print(cluster_sorted[j][0],cluster_sorted[j][1] )
                    x=cluster_sorted[j][0]
                    y=cluster_sorted[j][1]
                    sp_num=int(x/2)*128 + int(y/4)
                    toa_seed=(cluster_sorted[j][2]-toa_at_max_tot)*25
                    f.write("%2d\t%3d\t%3d\t%6.4f\t%6.6f\t%6.2f\t%4.3f\t"%(j,x,y,cluster_sorted[j][4],cluster_sorted[j][2],cluster_sorted[j][3],toa_seed))
                    f.write("%6d\t%3d\t%3d\t%3d\t%3d\t%3d\t%3d\t"%(cluster_sorted[j][6],cluster_sorted[j][7],cluster_sorted[j][8],cluster_sorted[j][9],cluster_sorted[j][10],cluster_sorted[j][11],cluster_sorted[j][12]))
                    f.write("(%1d)\n"%(cluster_sorted[j][13]))

                    uftoa_start_hist.append(cluster_sorted[j][7])
                    uftoa_stop_hist.append(cluster_sorted[j][8])
                    ftoa_rise_hist.append(cluster_sorted[j][9])
                    ftoa_fall_hist.append(cluster_sorted[j][10])

                    toa_ref0[x][y]=toa_seed

                    xx=cluster_sorted[j][0]-X+15
                    yy=cluster_sorted[j][1]-Y+15
                    if xx>0 and xx<30 and yy>0 and yy<30:
                        tot_map[xx][yy] += cluster_sorted[j][3]
                        toa_map[xx][yy] += (cluster_sorted[j][2]-toa_at_max_tot)*25
                        pc_map[xx][yy] += 1
                    else:
                        print (i,cluster_sorted[j], max_tot,toa_at_max_tot, xx,yy)

                    if cluster_sorted[j][3] > 0.5 and toa_seed < 150 and toa_seed > -150:
                        data_TOT_TOA.append([cluster_sorted[j][3],(cluster_sorted[j][2]-toa_at_max_tot)*25])

                    if toa_seed < -1:
                        neg_timing=True

                if not neg_timing:
                    alphas_pos_timing += 1
                else:
                    for j in range(len(cluster_sorted)):
                        x=cluster_sorted[j][0]
                        y=cluster_sorted[j][1]
                        # toa_seed=(cluster_sorted[j][2]-toa_at_max_tot)*25
                        # toa_neg_map[x][y]+=1
                        # print(toa_neg_map[x][y])
        f.close()

        fig, axs = plt.subplots(1, 1, figsize = (10,10))
        bc = axs.imshow(np.flip(np.rot90(toa_neg_map),0), cmap=plt.cm.bone_r, origin='lower',vmin=0,vmax=5)
        divider3 = make_axes_locatable(axs)
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%d")
        axs.set_title("TOA_neg")
        axs.set_ylabel("Rows")
        axs.set_xlabel("Columns")

        fig, axs = plt.subplots(2, 2, figsize = (10,10))
        counts, bins = np.histogram(uftoa_start_hist,bins=np.arange(0,8,1),density=True)
        axs[0][0].hist(bins[:-1], bins, weights=counts, facecolor='g', alpha=0.75,)
        axs[0][0].set_title("Histogram UFTOA-START")
        axs[0][0].set_ylabel("counts")
        axs[0][0].set_xlabel("bin")
        axs[0][0].grid(True)

        counts, bins = np.histogram(uftoa_stop_hist,bins=np.arange(0,8,1),density=True)
        axs[0][1].hist(bins[:-1], bins, weights=counts, facecolor='g', alpha=0.75,)
        axs[0][1].set_title("Histogram UFTOA-STOP")
        axs[0][1].set_ylabel("counts")
        axs[0][1].set_xlabel("bin")
        axs[0][1].grid(True)

        counts, bins = np.histogram(ftoa_rise_hist,bins=np.arange(0,31,1),density=True)
        axs[1][0].hist(bins[:-1], bins, weights=counts, facecolor='g', alpha=0.75,)
        axs[1][0].set_title("Histogram FTOA-RISE")
        axs[1][0].set_ylabel("counts")
        axs[1][0].set_xlabel("bin")
        axs[1][0].grid(True)

        counts, bins = np.histogram(ftoa_fall_hist,bins=np.arange(0,31,1),density=True)
        axs[1][1].hist(bins[:-1], bins, weights=counts, facecolor='g', alpha=0.75,)
        axs[1][1].set_title("Histogram FTOA-FALL")
        axs[1][1].set_ylabel("counts")
        axs[1][1].set_xlabel("bin")
        axs[1][1].grid(True)

        data_TOT_TOA=np.asarray(data_TOT_TOA, dtype=np.float)
        print(data_TOT_TOA[:,0])
        # for x in range(0,30):
        #     for y in range(0,30):
        #         tot_map[x][y]=tot_map[x][y]/pc_map[x][y]
        #         toa_map[x][y]=toa_map[x][y]/pc_map[x][y]

        if DETECT_NOISY_PIXELS:
            pc_list=[]
            for X in range(0,ARRAY_SIZE_X):
                for Y in range(0,ARRAY_SIZE_Y):
                    if pc_m[X][Y] > 0:
                        pc_list.append([X,Y,pc_m[X][Y],equal[X][Y]])

            pc_list.sort(key=sort2)

            for i in range(0,len(pc_list)):
                if pc_list[i][2]>THRESHOLD_NOISY_PIXEL:
                    mask[pc_list[i][0]][pc_list[i][1]]=1
                print(pc_list[i])

            np.savetxt(fbase+"mask_equal_1.dat",mask,fmt="%d")

            fig, axs = plt.subplots(1, 1, figsize = (10,10))

            bc = axs.imshow(np.flip(np.rot90(mask),0), origin='lower', vmin=0, vmax=1)
            divider3 = make_axes_locatable(axs)
            cax3 = divider3.append_axes("right", size="5%", pad=0.05)
            cbar3 = plt.colorbar(bc, cax=cax3, format="%d")
            axs.set_title("MASK bit")
            axs.set_ylabel("Rows")
            axs.set_xlabel("Columns")

        print("Num of Masked pixels : %d (%.2f)"%( len(np.argwhere(mask>0)), len(np.argwhere(mask>0))*100./(ARRAY_SIZE_X*ARRAY_SIZE_Y) ))

        if SHIFT_EQCODE_NOISY_PIXELS:
            pc_list=[]
            for X in range(0,ARRAY_SIZE_X):
                for Y in range(0,ARRAY_SIZE_Y):
                    if pc_m[X][Y] > 0:
                        pc_list.append([X,Y,pc_m[X][Y],equal[X][Y]])
            pc_list.sort(key=sort2)
            for i in range(0,len(pc_list)):
                if pc_list[i][3]>0:
                    equal[pc_list[i][0]][pc_list[i][1]]-=1
                print(pc_list[i])
            np.savetxt(fbase+"equal_equal_1.dat",equal,fmt="%d")

        print("Num alphas:", alphas)
        print("Num alphas pos timing: %d (%.1f)"%(alphas_pos_timing,alphas_pos_timing*100./alphas ))
        print("Short TOT: %d/%d (%.2f)"%(tot_short_c,c_pack,tot_short_c*100./c_pack))
        # api.set_dll_clk(lock_threshold=1, toa_clk_edge=0, enable_toa=False, toa_bin_or_gray=True, bypass_center_pll=True, enable_cols=False, service=tpx4Service)
        # api.readout_control(Top=True, readout_enable=0, service=tpx4Service)
        # api.readout_control(Top=False, readout_enable=0, service=tpx4Service)

        fig, axs = plt.subplots(2, 4, figsize = (20,10))

        bc = axs[0][0].imshow(np.flip(np.rot90(tot_m),0), origin='lower', vmin=0, vmax=200)
        divider3 = make_axes_locatable(axs[0][0])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%d")
        axs[0][0].set_title("TOT")
        axs[0][0].set_ylabel("Rows")
        axs[0][0].set_xlabel("Columns")
        np.savetxt(fbase +  'TOT_DD_%de_%3.2fs.txt'%(THR_e,SHUTTER_TIME_ON) , np.flip(np.rot90(tot_m),0) , fmt="%.3f")
        # fig, axs = plt.subplots(1, 1, figsize = (10,10))

        bt = axs[0][1].imshow(np.flip(np.rot90(toa_m),0), origin='lower') #, vmin=target-5, vmax=target+5)
        divider3 = make_axes_locatable(axs[0][1])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bt, cax=cax3, format="%d")
        axs[0][1].set_title("TOA")
        axs[0][1].set_ylabel("Rows")
        axs[0][1].set_xlabel("Columns")
        np.savetxt(fbase +  'TOA_DD_%de_%3.2fs.txt'%(THR_e,SHUTTER_TIME_ON) , np.flip(np.rot90(toa_m),0) , fmt="%.3f")
        np.savetxt(fbase +  'TOA_REF0_DD_%de_%3.2fs.txt'%(THR_e,SHUTTER_TIME_ON) , np.flip(np.rot90(toa_ref0),0) , fmt="%.3f")

        # fig, axs = plt.subplots(1, 1, figsize = (10,10))

        bt = axs[1][0].imshow(np.flip(np.rot90(pc_m),0), origin='lower', vmin=0, vmax=5)
        divider3 = make_axes_locatable(axs[1][0])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bt, cax=cax3, format="%d")
        axs[1][0].set_title("PC")
        axs[1][0].set_ylabel("Rows")
        axs[1][0].set_xlabel("Columns")
        # np.savetxt(fbase+'PC.csv', pc_m, delimiter='\t', fmt='%d')

        # bc = axs[1][1].imshow(np.flip(np.rot90(tot_map[0:30,0:30]),0), origin='lower',norm=colors.LogNorm(vmin=0.1, vmax=1000))
        # divider3 = make_axes_locatable(axs[1][1])
        # cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        # cbar3 = plt.colorbar(bc, cax=cax3, format="%.0f")
        # axs[1][1].set_title("TOT averaged (%d)"%alphas)
        # axs[1][1].set_ylabel("Rows")
        # axs[1][1].set_xlabel("Columns")
        #
        # bc = axs[1][2].imshow(np.flip(np.rot90(toa_map[0:30,0:30]),0), origin='lower',  norm=colors.SymLogNorm(linthresh=1, linscale=1,
        #                                       vmin=-25.0, vmax=25.0), cmap='RdBu_r') #norm=LogNorm(vmin=0.01, vmax=50))
        # divider3 = make_axes_locatable(axs[1][2])
        # cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        # cbar3 = plt.colorbar(bc, cax=cax3, format="%.1f")
        # axs[1][2].set_title("TOA averaged (%d)"%alphas)
        # axs[1][2].set_ylabel("Rows")
        # axs[1][2].set_xlabel("Columns")

        # npa = np.asarray(tot_hist, dtype=np.int)
        # npa = np.asarray(tot_hist_clusters, dtype=np.int)
        # mean_npa=np.mean(npa)

        # print(tot_hist_clusters)
        # print(mean_npa)
        # print(counts)
        # print(bins)
        tot_hist_clusters_all=[]
        for i in range (CLUSTER_SIZE_ACCEPTANCE_MIN, CLUSTER_SIZE_ACCEPTANCE_MAX):
            tot_hist_clusters_all += tot_hist_clusters[i]
            counts, bins = np.histogram(tot_hist_clusters[i],bins=np.arange(0,MAX_keV,MAX_keV/200),density=False)
            if i==CLUSTER_SIZE_ACCEPTANCE_MIN :
                hists=np.column_stack((bins[0:-1],counts*100))
            else:
                hists=np.column_stack((hists,counts*100))
        np.savetxt(fbase+'hist.txt', hists , delimiter='\t', fmt='%.2f')

        counts, bins = np.histogram(tot_hist_clusters_all,bins=np.arange(0,MAX_keV,MAX_keV/200),density=False)
        axs[0][2].hist(bins[:-1], bins, weights=counts,label='TOT (%d)'%len(tot_hist_clusters_all),histtype='bar')
        # axs[1][1].set_title("Histogram TOT %.2f"%(thr_val/1000.))
        axs[0][2].set_ylabel("counts")
        axs[0][2].set_xlabel("[ns]")
        axs[0][2].legend(loc='upper left')
        axs[0][2].grid(True)

        counts, bins = np.histogram(tot_hist_clusters_size,bins=np.arange(0,CLUSTER_SIZE_ACCEPTANCE_MAX,1),density=False)

        axs[0][3].hist(bins[:-1], bins, weights=counts,label='Cluster size (%d)'%len(tot_hist_clusters_size),histtype='bar')
        # axs[1][1].set_title("Histogram TOT %.2f"%(thr_val/1000.))
        axs[0][3].set_ylabel("counts")
        axs[0][3].set_xlabel("size")
        axs[0][3].legend(loc='upper left')
        axs[0][3].grid(True)

        bc = axs[1][3].imshow(np.flip(np.rot90(pc_map[0:30,0:30]),0), origin='lower', norm=colors.LogNorm(vmin=1))
        divider3 = make_axes_locatable(axs[1][3])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%d")
        axs[1][3].set_title("PC (%d)"%alphas)
        axs[1][3].set_ylabel("Rows")
        axs[1][3].set_xlabel("Columns")

        fig, axs2 = plt.subplots(1, 1, figsize = (10,10))

        counts, xedges, yedges, im  = axs2.hist2d(data_TOT_TOA[:,0],data_TOT_TOA[:,1], bins=200,range=[[0,MAX_keV],[-30,60]],
                                                  cmin=0, cmap=plt.cm.jet, norm=colors.LogNorm(vmin=1, vmax=alphas/10))
        axs2.set_title("Hist2D TOA-TOT")
        axs2.set_ylabel("TOA [ns]")
        axs2.set_xlabel("TOT [25ns]")
        print(im)
        fig.colorbar(im)
        # axs2.set_ylim([-10,50])

        fig, axs = plt.subplots(1, 1, figsize = (10,10))

        bc = axs.imshow(np.flip(np.rot90(pc_m),0), origin='lower', vmin=0, vmax=10)
        divider3 = make_axes_locatable(axs)
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%d")
        axs.set_title("PC")
        axs.set_ylabel("Rows")
        axs.set_xlabel("Columns")
        # plt.savefig(fbase + "PC_THR_DD_%d.png"%THR_e)
        np.savetxt(fbase +  'PC_THR_DD_%d.txt'%(THR_e) , np.flip(np.rot90(pc_m),0) , fmt="%d")


        plt.tight_layout()
        # plt.show()
