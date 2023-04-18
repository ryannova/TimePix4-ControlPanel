import grpc
import rpc
import api as api

def DACs(DAC_I, DAC_VB, DAC_VT):
    #    (I=0,V=1,buffer, top, center, bottom), reg_to_set, title, bits, default value, reverseDACCode, reverseDACGain
    DAC_I.append( [0, (0x2, 0x0, 0x6, 0x0), 0xa007, "VBiasPreamp",         8, 80, 16, 1])
    DAC_I.append( [0, (0x2, 0x0, 0x7, 0x0), 0xa004, "VbiasDiscTailNMOS",   8, 50, 16, 1])
    DAC_I.append( [0, (0x2, 0x0, 0x8, 0x0), 0xa005, "VBiasIkrum",          8, 10, 10, 10])
    DAC_I.append( [0, (0x2, 0x0, 0x9, 0x0), 0xa001, "VBiasDAC",            8, 45, 16, 1])
    DAC_I.append( [0, (0x2, 0x0, 0xa, 0x0), 0xa006, "VBiasLevelShift",     8, 40, 16, 1])
    DAC_I.append( [0, (0x2, 0x0, 0xb, 0x0), 0xa002, "VbiasDiscPMOS",       8, 50, 16, 1])
    DAC_I.append( [0, (0x2, 0x0, 0xc, 0x0), 0xa003, "VbiasDiscTRAFF",      8, 50, 16, 1])
    DAC_I.append( [0, (0x2, 0x0, 0xd, 0x0), 0xa000, "VbiasADC",            8, 128, 128, 32])

    DAC_VB.append( [1, (0x2, 0x0, 0xe, 0x0), 0xa009, "VcascPreamp_BOT",     8, 170, 0, 1, 0xa011, 0x5])
    DAC_VB.append( [1, (0x2, 0x0, 0xf, 0x0), 0xa00b, "VFBK_BOT",            8, 128, 1, 1, 0xa013, 0x2])
    DAC_VB.append( [1, (0x2, 0x0, 0x10, 0x0), 0xa00d, "VTP_Coarse_BOT",     8, 128, 1, 1, 0xa015, 0x2])
    DAC_VB.append( [1, (0x2, 0x0, 0x11, 0x0), 0xa008, "VcascDisc_BOT",      8, 130, 1, 0, 0xa010, 0x5])
    DAC_VB.append( [1, (0x2, 0x0, 0x12, 0x0), 0xa00a, "VcontrolVCO_BOT",    8, 0, 1, 0, 0xa012, 0x2])
    DAC_VB.append( [1, (0x2, 0x0, 0x13, 0x0), 0xa00c, "Vthreshold_BOT",     10,2**13, 0, 0, 0xa014, 0x5])
    DAC_VB.append( [1, (0x2, 0x0, 0x14, 0x0), 0xa00e, "VTP_Fine_BOT",       10,512, 0, 0, 0xa016, 0x5])

    DAC_VT.append( [1, (0x2, 0x0, 0x15, 0x0), 0xa009, "VcascPreamp_TOP",    8, 170, 0, 1, 0xa011, 0x5])
    DAC_VT.append( [1, (0x2, 0x0, 0x16, 0x0), 0xa00b, "VFBK_TOP",           8, 128, 1, 1, 0xa013, 0x2])
    DAC_VT.append( [1, (0x2, 0x0, 0x17, 0x0), 0xa00d, "VTP_Coarse_TOP",     8, 128, 1, 1, 0xa015, 0x2])
    DAC_VT.append( [1, (0x2, 0x0, 0x18, 0x0), 0xa008, "VcascDisc_TOP",      8, 130, 1, 0, 0xa010, 0x5])
    DAC_VT.append( [1, (0x2, 0x0, 0x19, 0x0), 0xa00a, "VcontrolVCO_TOP",    8, 0, 1, 0, 0xa012, 0x2])
    DAC_VT.append( [1, (0x2, 0x0, 0x1a, 0x0), 0xa00c, "Vthreshold_TOP",     10,2**13, 0, 0, 0xa014, 0x5])
    DAC_VT.append( [1, (0x2, 0x0, 0x14, 0x0), 0xa00e, "VTP_Fine_TOP",       10,512, 0, 0, 0xa016, 0x5])

def table_DACs_to_AEOC_DACs():
    #Relates DAC number and AEOC address for each DAC
    # return [[0,6],[1,4],[2,5],[3,3],[4,2],[5,1],[6,0]]
    return [6,4,5,3,2,1,0]

def table_AEOCDACs_to_DACs():
    #Relates DAC number and AEOC address for each DAC
    return [0,1,2,3,5,4,6,7,8,9]

def AEOC_DACs(AEOC_DAC):
    AEOC_DAC.append([0,'VbiasDiscTRAFF'])
    AEOC_DAC.append([1,'VbiasDiscPMOS'])
    AEOC_DAC.append([2,'VbiasLevelShiftPMOS'])
    AEOC_DAC.append([3,'VbiasDAC_bias'])
    AEOC_DAC.append([4,'VbiasDiscTailNMOS'])
    AEOC_DAC.append([5,'VbiasIkrum'])
    AEOC_DAC.append([6,'VbiasPreamp'])
    AEOC_DAC.append([7,'VCO_Vcontrol'])
    AEOC_DAC.append([8,'PS_monitor_analog_AEOC_13'])
    AEOC_DAC.append([9,'PS_monitor_analog_AEOC_23'])

def DACs_set_default(DAC_I, DAC_VB, DAC_VT, PowerMode, service):
    low_power=[5,6,7]
    print('###############Setting default values to all Master DACs###############')
    for n in range(0, len(DAC_I)):
        service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC_I[n][2], val=DAC_I[n][low_power[PowerMode]]))

    for n in range(0, len(DAC_VB)):
        default_val = DAC_VB[n][5]
        if (DAC_VB[n][6]):
            default_val = api.reverse_Bits(DAC_VB[n][5],DAC_VB[n][4])
        service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC_VB[n][2], val=default_val))
        default_gain_val = DAC_VB[n][9]
        if (DAC_VB[n][7]):
            default_gain_val = api.reverse_Bits(default_gain_val,4)
        service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC_VB[n][8], val=default_gain_val))

    for n in range(0, len(DAC_VT)):
        default_val = DAC_VT[n][5]
        if (DAC_VT[n][6]):
            default_val = api.reverse_Bits(DAC_VT[n][5],DAC_VT[n][4])
        service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC_VT[n][2], val=default_val))
        default_gain_val =  DAC_VT[n][9]
        if (DAC_VT[n][7]):
            default_gain_val = api.reverse_Bits(default_gain_val,4)
        service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC_VT[n][8], val=default_gain_val))

def Read_DACs(DAC_I, DAC_VB, DAC_VT, OSR, service):
    print('###############Reading all Master DACs###############')
    for n in range(0, len(DAC_I)):
        api.setDacOut(DAC_I[n][1],0,service)
        dac_code=rpc.decode_u16(service.ReadReg(rpc.ReadRegRequest(addr=DAC_I[n][2])).data)
        print('%s\t%d\t%.3f' %(DAC_I[n][3],dac_code,api.ADC_Sample(OSR, 0, service)))
    for n in range(0, len(DAC_VB)):
        api.setDacOut(DAC_VB[n][1],0,service)
        dac_code=rpc.decode_u16(service.ReadReg(rpc.ReadRegRequest(addr=DAC_VB[n][2])).data)
        if DAC_VB[n][6]:
            dac_code=api.reverse_Bits(dac_code,DAC_VB[n][4])
        dac_code_gain=rpc.decode_u16(service.ReadReg(rpc.ReadRegRequest(addr=DAC_VB[n][8])).data)
        if (DAC_VB[n][7]):
            dac_code_gain=api.reverse_Bits(dac_code_gain,4)
        print('%s\t%d\t%d\t%.3f' %(DAC_VB[n][3],dac_code,dac_code_gain,api.ADC_Sample(OSR, 0, service)))
    for n in range(0, len(DAC_VT)):
        api.setDacOut(DAC_VT[n][1],0,service)
        dac_code=rpc.decode_u16(service.ReadReg(rpc.ReadRegRequest(addr=DAC_VT[n][2])).data)
        if DAC_VT[n][6]:
            dac_code=api.reverse_Bits(dac_code,DAC_VT[n][4])
        dac_code_gain=rpc.decode_u16(service.ReadReg(rpc.ReadRegRequest(addr=DAC_VT[n][8])).data)
        if (DAC_VT[n][7]):
            dac_code_gain=api.reverse_Bits(dac_code_gain,4)
        print('%s\t%d\t%d\t%.3f' %(DAC_VT[n][3],dac_code,dac_code_gain,api.ADC_Sample(OSR, 0, service)))

def Read_AEOC_vals(AEOC, aeoc_addr, top, OSR, service):
    if top:
        sel_dacout_buffer=0x1
    else:
        sel_dacout_buffer=0x3
    for n in range(0, len(AEOC)):
        selection=(sel_dacout_buffer,AEOC[n][0],0,AEOC[n][0])
        api.setDacOut(selection,aeoc_addr,service)
        print('%s[%d]\t%.3f' %(AEOC[n][1],aeoc_addr,api.ADC_Sample(OSR, 0, service)))

def Read_AEOC_vals_1DAC(AEOC, DAC_num, aeoc_addr, top, OSR, print_val, service):
    if top:
        sel_dacout_buffer=0x1
    else:
        sel_dacout_buffer=0x3
    selection=(sel_dacout_buffer,AEOC[DAC_num][0],0,AEOC[DAC_num][0])
    api.setDacOut(selection,aeoc_addr,service)
    adc=api.ADC_Sample(OSR, 0, service)
    if print_val:
        print('%s[%d]\t%.3f' %(AEOC[DAC_num][1],aeoc_addr,adc))
    return (adc)


def Set_DAC(DAC=0, val=0, sampleADC=False, OSR=0, service=0, print_enable=True):
    p_out='%s --> %d '%(DAC[3],val)
    adc_sample=0
    if len(DAC)>8: #is voltage DAC
        if DAC[6]:
            val= api.reverse_Bits(val,DAC[4])
        val_gain=DAC[9]
        if DAC[7]:
            val_gain=api.reverse_Bits(val_gain,4)
        service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC[8], val=val_gain))
    service.SimpleWrite(rpc.SimpleWriteRequest(addr=DAC[2], val=val))
    if sampleADC:
        api.setDacOut(DAC[1],0,service)
        adc_sample=api.ADC_Sample(OSR, 0.0, service)
        p_out += ' %.6f' %adc_sample
    if print_enable:
        print(p_out)
    return adc_sample

def SupplyCenter(OSR=0,service=0):
    position=[0.27,8.3,16.33,24.36]
    vddagnda=""
    vddgnd=""
    pos=""
    print("#############################################")
    for i in range(0,4):
        PS_val_ana=api.PS_monitor_center(addr_13=0x1c + i, addr_23=0x20 + i, OSR=OSR, service=service, printVal=True)
        pos+="\t%2.2f"%position[i]
        vddagnda+="\t%2.3f"%(PS_val_ana)
    for i in range(0,4):
        PS_val_dig=api.PS_monitor_center(addr_13=0x24 + i, addr_23=0x28 + i, OSR=OSR, service=service, printVal=True)
        vddgnd+="\t%2.3f"%(PS_val_dig)
    print("X[mm]    ",pos)
    print("VDDA-GNDA[V]",vddagnda)
    print("VDD-GND  [V]",vddgnd)
    print("#############################################")
    # print("@%d VDDA-GNDA = %.3f V VDD-GND = %.3f V"%(position[i],PS_val_ana,PS_val_dig))

    return
