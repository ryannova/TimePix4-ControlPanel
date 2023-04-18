import grpc
import rpc
import matplotlib.pyplot as plt
import numpy as np
import time
import xavi_config as ec
import api as api
import dacs as dacs
import struct
import matrix as mat
import conf_timepix4 as conf_tpix4

if __name__ == '__main__':

    EMPTY = rpc.Empty()
    with grpc.insecure_channel(ec.TIMEPIX_ADDRESS) as channel:

        # We'll assume Timepix 4 is located at index 0
        tpx4Service = rpc.Timepix4Stub(channel)
        peripheralService = rpc.PeripheralStub(channel)
        controlService = rpc.ControlInfoStub(channel)

        fbase='./examples/'

        DAC_I, DAC_VB, DAC_VT, AEOC, OSR = conf_tpix4.conf_timepix4(fbase=fbase,
                                                                    GRAY_COUNTER=True,
                                                                    BYPASS_CENTER=True,
                                                                    BYPASS_DAC_SETTING=False,
                                                                    POLARITY=True,
                                                                    POWER_MODE=1,
                                                                    ENABLE_STATUS_PROC=False,
                                                                    ENABLE_DLL_COLS=True,
                                                                    ENABLE_TOA=True,
                                                                    ENABLE_TDC=True,
                                                                    service=tpx4Service,
                                                                    peripheral=peripheralService,
                                                                    control=controlService)


        fig, ax1 = plt.subplots(1, 1, figsize = (10,4))
        cols=[]
        counter_unlocks=[]
        ARRAY_SIZE_X=448
        NUM_THR=1
        NUM_EVENTS=1
        eoc_dll=np.zeros(shape=(int(ARRAY_SIZE_X/2.),NUM_THR+1), dtype='int')

        for thr in range(1,NUM_THR+1):
            dllB =[]
            dllT =[]
            x=[]
            api.set_dll_clk(lock_threshold=thr, toa_clk_edge=1 , clk_dll_freq_sel=0x0, enable_toa=True, toa_bin_or_gray=True, bypass_center_pll=True,
            enable_cols=True, service=tpx4Service)
            for j in range(0,1):
                for n in range(0,224):
                    x.append(n)
                    top=[]
                    bot=[]
                    for events in range(0,NUM_EVENTS):
                        # api.set_dll_clk(lock_threshold=thr, toa_clk_edge=1 , clk_dll_freq_sel=0x0, enable_toa=True, toa_bin_or_gray=True, bypass_center_pll=True,
                        # enable_cols=True, service=tpx4Service)
                        api.power_up_dll(service=tpx4Service)
                        eoc_bot = rpc.decode_u16(tpx4Service.ReadReg(rpc.ReadRegRequest(idx=0, addr=0x8100 + n, count=1)).data)
                        eoc_top = rpc.decode_u16(tpx4Service.ReadReg(rpc.ReadRegRequest(idx=0, addr=0x8200 + n, count=1)).data)
                        top.append(api.decodeDLL(eoc_top))
                        bot.append(api.decodeDLL(eoc_bot))
                    dllB.append(np.average(bot))
                    dllT.append(np.average(top))
                    print ('%d\t%d\t%d\t%.2f\t%.2f\t%d\t%.2f\t%.2f\t%d' %(thr,j, n, dllB[-1], np.std(bot), api.DLL_is_locked(eoc_bot), dllT[-1],  np.std(top), api.DLL_is_locked(eoc_top)))
            plt.plot(x, dllB,label='BOT_%d'%(NUM_EVENTS))
            plt.plot(x, dllT,label='TOP_%d'%(NUM_EVENTS))
            # for col in range(0,224):
            #     c_unlock=0
            #     eoc_dll[col][0]=col
            #     for n in range(0,500):
            #         eoc_bot = rpc.decode_u16(tpx4Service.ReadReg(rpc.ReadRegRequest(idx=0, addr=0x8100 + col, count=1)).data)
            #         if not api.DLL_is_locked(eoc_bot):
            #             c_unlock+=1
            #             print ('%d\t%d\t%d\t%d\t%d' %(col,thr, n, api.decodeDLL(eoc_bot), api.DLL_is_locked(eoc_bot)))
            #             eoc_dll
            #             # dllB.append(api.decodeDLL(eoc_bot))
            #             # dllT.append(api.DLL_is_locked(eoc_bot))
            #     eoc_dll[col][thr+1]=c_unlock
        # x=[]
        # y=[]
        # for col in range(0,224):
        #     x.append(eoc_dll[col][0])
        #     y.append(eoc_dll[col][1])
        # print(eoc_dll[0], eoc_dll[1])
        # ax1[0].plot(x, y,label='DLL_VAL_%d_%d'%(thr,col))
        # ax1[1].plot(eoc_dll[0], eoc_dll[2],label='LOCK_%d_%d'%(thr,col))

        # print(eoc_dll)


        # api.set_dll_clk(lock_threshold=1, enable_toa=False, toa_bin_or_gray=True, bypass_center_pll=True, enable_cols=False, service=tpx4Service)

        # dacs.Read_DACs(DAC_I, DAC_VB, DAC_VT, OSR, tpx4Service)

        # plot!
        plt.title('DLL')
        plt.xlabel("EOC")
        plt.ylabel("code")
        # plt.xlim([0,224])
        plt.grid(True)
        plt.legend(loc='upper left')#, bbox_to_anchor=(1.0,1))
        plt.show()
