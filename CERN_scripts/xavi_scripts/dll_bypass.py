import grpc
import rpc
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm
from matplotlib.ticker import MultipleLocator
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

        # DAC_I = []
        # DAC_VB = []
        # DAC_VT = []
        # dacs.DACs(DAC_I, DAC_VB, DAC_VT)
        # dacs.DACs_set_default(DAC_I, DAC_VB, DAC_VT,tpx4Service)
        #
        #
        #
        # api.set_dll_clk(lock_threshold=1, enable_toa=False, toa_bin_or_gray=True, bypass_center_pll=0, enable_cols=True, service=tpx4Service)
        # api.power_up_dll(tpx4Service)

        fbase='./examples/'

        DAC_I, DAC_VB, DAC_VT, AEOC, OSR = conf_tpix4.conf_timepix4(fbase=fbase,
                                                                    GRAY_COUNTER=True,
                                                                    BYPASS_CENTER=True,
                                                                    POLARITY=True,
                                                                    ENABLE_STATUS_PROC=False,
                                                                    ENABLE_TOA=False,
                                                                    ENABLE_TDC=False,
                                                                    service=tpx4Service,
                                                                    peripheral=peripheralService,
                                                                    control=controlService)

        dllB = {}
        dllT = {}
        for n in range(0,224):
            dllB[n] = []
            dllT[n] = []
        x = []
        f=open('dll_bypass_top.txt','w')
        f2=open('dll_bypass_bot.txt','w')
        dll_bypassed= np.zeros(shape=(448,32), dtype=int)
        dll_bypassed_diff= np.zeros(shape=(448,32), dtype=int)
        dll_locked= np.zeros(shape=(448,32), dtype=int)
        for j in range(0,33,1):
            x.append(j)
            SPColConfig = np.zeros(3*16, dtype=np.uint8)

            if j<16:
                bypass_up=True #
                bypass_down=False
                row=j
                ii=0
            if j<32 and j>=16:
                bypass_up=False
                bypass_down=True #
                row=31-j
                ii=1

            for n in range(0,len(SPColConfig),3):
                if (1):
                    if (int(n/3)==row):
                        if bypass_down:
                            SPColConfig[n]=0x2         #0x2 bypass_down
                        if bypass_up:
                            SPColConfig[n+1]=0x8        #0x8 bypass_up

            if j>31:
                SPColConfig = np.zeros(3*16, dtype=np.uint8)

            # print (SPColConfig.tobytes())
            for n in range(0,224):
                tpx4Service.WriteReg(rpc.WriteRegRequest(idx=0, addr=0x7000+n, data=SPColConfig.tobytes(), count=1))
                tpx4Service.WriteReg(rpc.WriteRegRequest(idx=0, addr=0xF000+n, data=SPColConfig.tobytes(), count=1))

            api.power_up_dll(tpx4Service)
            f.write('%d\t'%j)
            f2.write('%d\t'%j)

            for n in range(0,224):
                eoc_bot = rpc.decode_u16(tpx4Service.ReadReg(rpc.ReadRegRequest(idx=0, addr=0x8100 + n, count=1)).data)
                eoc_top = rpc.decode_u16(tpx4Service.ReadReg(rpc.ReadRegRequest(idx=0, addr=0x8200 + n, count=1)).data)
                if j<32:
                    dll_bypassed[n*2+ii][15-row]=api.decodeDLL(eoc_bot)
                    dll_bypassed[n*2+ii][16+row]=api.decodeDLL(eoc_top)
                else:
                    for sp in range(0,16):
                        dll_locked[n*2][sp] = api.decodeDLL(eoc_bot)
                        dll_locked[n*2+1][sp] = api.decodeDLL(eoc_bot)
                        dll_locked[n*2][sp+16] = api.decodeDLL(eoc_top)
                        dll_locked[n*2+1][sp+16] = api.decodeDLL(eoc_top)

                f.write('%d\t' %api.decodeDLL(eoc_top))
                f2.write('%d\t' %api.decodeDLL(eoc_bot))
                print ('%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d' %(j, n, bypass_up,bypass_down, api.decodeDLL(eoc_bot), api.DLL_is_locked(eoc_bot), api.decodeDLL(eoc_top), api.DLL_is_locked(eoc_top)))
                dllB[n].append(api.decodeDLL(eoc_bot))
                dllT[n].append(api.decodeDLL(eoc_top))
            f.write('\n')
            f2.write('\n')

        api.set_dll_clk(lock_threshold=1, enable_toa=False, toa_bin_or_gray=True, bypass_center_pll=1, enable_cols=False, service=tpx4Service)

        for n in range(0,224):
            tpx4Service.WriteReg(rpc.WriteRegRequest(idx=0, addr=0x7000+n, data=np.zeros(3*16, dtype=np.uint8).tobytes(), count=1))
            tpx4Service.WriteReg(rpc.WriteRegRequest(idx=0, addr=0xF000+n, data=np.zeros(3*16, dtype=np.uint8).tobytes(), count=1))


        f.close()
        f2.close()

        for i in range(0,448):
            for j in range(0,32):
                dll_bypassed_diff[i][j] = dll_bypassed[i][j] - dll_locked[i][j]

        fig, axs = plt.subplots(3, 1, figsize = (15,5))

        # bc = axs[0].imshow(np.flip(np.rot90(intercept),0), origin='lower', vmin=int(intercept_a)-50, vmax=int(intercept_a)+50)
        bc = axs[0].imshow(np.rot90(dll_bypassed), origin='lower')
        divider3 = make_axes_locatable(axs[0])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%.2f")
        axs[0].set_title("DLL_locked_bypass1")
        axs[0].set_ylabel("SP")
        axs[0].set_xlabel("Columns")

        bc = axs[1].imshow(np.rot90(dll_bypassed_diff), origin='lower')
        divider3 = make_axes_locatable(axs[1])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%.2f")
        axs[1].set_title("DLL_locked_bypass1_diff")
        axs[1].set_ylabel("SP")
        axs[1].set_xlabel("Columns")


        bc = axs[2].imshow(np.rot90(dll_locked), origin='lower')
        divider3 = make_axes_locatable(axs[2])
        cax3 = divider3.append_axes("right", size="5%", pad=0.05)
        cbar3 = plt.colorbar(bc, cax=cax3, format="%.2f")
        axs[2].set_title("DLL_locked")
        axs[2].set_ylabel("SP")
        axs[2].set_xlabel("Columns")

        print(dll_bypassed)
        # plot!
        plt.figure(figsize = (10,10))
        plt.title('DLL')
        for per in [0,1]:
            for n in range(0,224):
                if per==0:
                    ll= dllB[n]
                else:
                    ll= dllT[n]

                fx_max = np.max([ x - ll[-1] for x in ll ][0:-1], axis=0)
                fx_min = np.min([ x - ll[-1] for x in ll ][0:-1], axis=0)

                if fx_max-fx_min>1:
                    print (per, n,":", fx_max, fx_min, ll[-1],ll)
                    plt.plot(x[0:-1], [ x - ll[-1] for x in ll ][0:-1])
                    # plt.plot(x, dllT[n])
                else:
                    print (per, n,":", fx_max, fx_min, ll[-1])

        #plt.plot(x, coarseB)
        #plt.plot(x, coarseB)
        plt.xlabel("SPGroup")
        plt.ylabel("code")
        plt.show()
