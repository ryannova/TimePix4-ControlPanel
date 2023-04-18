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

if __name__ == '__main__':

    EMPTY = rpc.Empty()
    with grpc.insecure_channel(ec.TIMEPIX_ADDRESS) as channel:

        # We'll assume Timepix 4 is located at index 0
        tpx4Service = rpc.Timepix4Stub(channel)
        peripheralService = rpc.PeripheralStub(channel)
        controlService = rpc.ControlInfoStub(channel)

        fbase='/home/timepix4/spidr4/spidr4_python/examples/'

        DAC_I, DAC_VB, DAC_VT, AEOC, OSR = conf_tpix4.conf_timepix4(fbase=fbase,
                                                                    GRAY_COUNTER=True,
                                                                    BYPASS_CENTER=True,
                                                                    OSR_CLOCK_REF=2**5,
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

        f=open('dac_scan.txt','w')
        fig, ax1 = plt.subplots(1, 1, figsize = (8,5))

        api.analog_periphery_reg(select_VCO_control=1, select_Polarity_or_LogGainEn=1,  service=tpx4Service)

        INL=False
        for dac in range(0,16,1):

            DAC_SCAN = DAC_VT[4]
            DAC_SCAN[9]=dac #vgain
            print(DAC_SCAN)
            read_back = []
            read_back_int = []
            read_ps0 = []
            read_ps1 = []
            read_ps2 = []
            read_ps3 = []
            # if INL:
            #     param_vtpcoarse=mat.linearize_DAC(DAC=DAC_SCAN, OSR=OSR, STEPS=32, service=tpx4Service)

            # Some generic settings
            DAC_VALUES = np.array(np.round(np.linspace(0, 2**DAC_SCAN[4]-1, 2**DAC_SCAN[4])), dtype=np.int)
            DAC_VALUES = np.array(np.round(np.linspace(0, 2**DAC_SCAN[4]-1, 32)), dtype=np.int)

            x=[]
            y=[]
            x_lin=[]

            for dac_val in DAC_VALUES:
                dac_val_int= dac_val
                aeoc_dac=0
                # aeoc_dac=dacs.Read_AEOC_vals_1DAC(AEOC, 3, 0, 1, OSR, False, tpx4Service)
                # Configure selection register
                # api.setDacOut(DAC_SCAN[1],0,tpx4Service)

                ADC_int=dacs.Set_DAC(DAC=DAC_SCAN, val=(0x2<<10)+dac_val, sampleADC=True, OSR=OSR, service=tpx4Service, print_enable=False)

                # table=dacs.table_DACsandAEOC_DACs()
                # AEOC_DAC_pos=table[2][1]
                # addr_AEOC=dac%112
                # top=int(dac/112)
                # ADC_int=dacs.Read_AEOC_vals_1DAC(AEOC, AEOC_DAC_pos, addr_AEOC, top=top, OSR=OSR, print_val=False, service=tpx4Service)
                # ADC_int=dacs.Read_AEOC_vals_1DAC(AEOC, 7, 10, 1, OSR, False, tpx4Service)
                PS_val_ana=0
                PS_val_dig=0
                temp=0
                # resp = peripheralService.SenseNow(rpc.StringList(items = [ SENSE_VALUE ]))
                x.append(dac_val)
                y.append(ADC_int)

                if 0:
                    PS_val_ana=api.PS_monitor_center(0x1e, 0x22, OSR, tpx4Service)
                    PS_val_dig=api.PS_monitor_center(0x26, 0x2a, OSR, tpx4Service)
                    # temp=api.Temperature(OSR,tpx4Service)

                s='%d\t%d\t%.6f\t%.6f\t%.3f\t%.3f\t%.3f\t' %(dac_val,OSR,ADC_int ,aeoc_dac, temp ,PS_val_ana,PS_val_dig)

                # Read ADC now
                # resp = peripheralService.SenseNow(rpc.StringList(items = [ SENSE_VALUE ]))
                read_ps0.append(PS_val_ana)
                # read_ps1.append(api.PS_monitor_center(0x1D, 0x21, OSR, tpx4Service))
                # read_ps2.append(api.PS_monitor_center(0x1E, 0x22, OSR, tpx4Service))
                # read_ps3.append(api.PS_monitor_center(0x1F, 0x23, OSR, tpx4Service))
                # # ADD response value
                #sread_back.append(resp.items[0].value.float_value)
                # s=s+'%.6f'%resp.items[0].value.float_value
                print (s)
                f.write(s + '\n')
                # Sleep to settle
                time.sleep(0.0)
                read_back_int.append(ADC_int)
            inl=[]
            params, params_covariance = optimize.curve_fit(mat.lin_fit, x, y)

            print(params)
            if INL:
                for i in range(0,len(x)):
                    inl.append((y[i]-(params[0]*x[i]+params[1]))/params[0])
                    x_lin.append(mat.lin_fit(x[i], params[0], params[1]))
                print (max(inl),min(inl))

            # Reset DAC to 0
            dacs.DACs_set_default(DAC_I, DAC_VB, DAC_VT, 1, tpx4Service)

            # plot!


            ax1.plot(DAC_VALUES, read_back_int,'o', label='%d: [%.3f mV/step] %s'%(dac,params[0]*1000, DAC_SCAN[3]))
            # ax1.plot(DAC_VALUES, read_back_int,':', label='%d %d %s'%(top,addr_AEOC,AEOC[AEOC_DAC_pos][1]))
            # ax1.plot(DAC_VALUES, read_back_int,'o:', label='%s'%DAC_SCAN[3])
            ax1.legend(loc='upper left', bbox_to_anchor=(1.1,1))
            if INL:
                ax1.plot(DAC_VALUES, x_lin,'r-')
                # ax2 = ax1.twinx()
                # ax2.set_ylabel('INL [LSB]', color='b')
                # ax2.plot(DAC_VALUES, inl,'b-')
                # ax2.set_ylim([-10,10])
            ax1.set_xlabel('DAC Code')
            ax1.set_ylabel('[V]', color='g')
            ax1.set_ylim([0,1.2])


        plt.tight_layout()
        plt.savefig('results/dac_v_gain.png',format='png')
        plt.show()

        f.close()
