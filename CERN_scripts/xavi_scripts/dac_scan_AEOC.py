import grpc
import rpc
import matplotlib.pyplot as plt
import numpy as np
import time
import xavi_config as ec
import api as api
import dacs as dacs
import matrix as mat
from scipy import optimize
import conf_timepix4 as conf_tpix4
import handy as handy

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
                                                                    OSR_CLOCK_REF=2**3,
                                                                    OSR_OSR=2**12,
                                                                    POLARITY=True,
                                                                    ENABLE_STATUS_PROC=False,
                                                                    ENABLE_TOA=False,
                                                                    ENABLE_TDC=False,
                                                                    service=tpx4Service,
                                                                    peripheral=peripheralService,
                                                                    control=controlService)

        pixelConfig = np.zeros(shape=(2,224,16,32), dtype=np.uint8)

        for X in range(0,448,1):
            for Y in range(0,512,1):
                addr=mat.addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
                pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=api.pixel_conf(dac_bits=15, power_enable=1, tp_enable=0, mask_bit=1)
        tpx4Service.ConfigPixels(rpc.Tpx4PixelConfig(idx = 0, config=pixelConfig.tobytes()))

        # Configure sensor value to read
        SENSE_VALUE =  'carrier/adc/volt'

        # param_vtpcoarse=mat.linearize_DAC(DAC=DAC_SCAN, OSR=OSR, STEPS=64, service=tpx4Service)

        f=open('dac_scan_aeoc.txt','w')
        fig, ax1 = plt.subplots(1, 1, figsize = (8,4))
        fig, ax2 = plt.subplots(1, 1, figsize = (12,4))

        api.analog_periphery_reg(select_VCO_control=1, select_Polarity_or_LogGainEn=1,  service=tpx4Service)

        # table=dacs.table_AEOCDACs_to_DACs()
        vals={}
        for aeoc in range (0,10):
            vals[aeoc]=[]
            AEOC_x=[]
            for cols in range (0,224):
                AEOC_x.append(cols)
                addr_AEOC=cols%112
                top=int(cols/112)
                # AEOC_DAC_pos=table[aeoc]
                ADC_int=dacs.Read_AEOC_vals_1DAC(AEOC, AEOC[aeoc][0], addr_AEOC, top=top, OSR=OSR, print_val=False, service=tpx4Service)
                if top:
                    print ("TOP %s %3d %1.3f"%(AEOC[aeoc][1],cols,ADC_int))
                else:
                    print ("BOT %s %3d %1.3f"%(AEOC[aeoc][1],cols,ADC_int))

                vals[aeoc].append(ADC_int)

            ax1.plot(AEOC_x, vals[aeoc],'o', label='%s'%(AEOC[aeoc][1]))
            ax1.legend(loc='upper left', bbox_to_anchor=(1.0,1))
            ax1.set_ylim([0,1.2])
            ax1.set_xlim([0,224])

        for aeoc in range (0,10):
            outliers=handy.detect_outlier(data_1=vals[aeoc], x=AEOC_x, threshold=5)
            if len(outliers)>1 :
                print("OUTLIERS\t","%s\t"%AEOC[aeoc][1],outliers)
        # print(list(3*map(operator.sub, vals[9], vals[8])))
        # print(set(vals[9]) - set(vals[8]))
        VDDA_GNDA=[]
        for i in range(0,len(AEOC_x)):
            VDDA_GNDA.append(3*(vals[9][i] - vals[8][i]))
        ax2.plot(AEOC_x, VDDA_GNDA,'o', label='AEOC VDDA-GNDA')
        ax2.legend(loc='upper left', bbox_to_anchor=(1.1,1))
        ax2.set_ylim([1.1,1.3])
        ax2.set_xlim([0,224])

        plt.tight_layout()
        # plt.savefig('results/dac_v_gain.png',format='png')
        plt.show()
        f.close()
