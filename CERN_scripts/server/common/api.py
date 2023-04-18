import vcu128
import matplotlib.pyplot as plt
import numpy as np
import time
import dacs
import math
#import examples_config as ec

#Sets SLVS termination deppending side used
def set_conf_io(side):
    if side=='top':
        SimpleWriteRequest(addr=0xcc04, val=0x0eaa)
        SimpleWriteRequest(addr=0x4c04, val=0x0955)
        SimpleWriteRequest(addr=0xac04, val=0x0955)
    if side=='bot':
        SimpleWriteRequest(addr=0x4c04, val=0x0eaa)
        #Nikhef board has clkref in both sides
        SimpleWriteRequest(addr=0xcc04, val=0x1965)
        SimpleWriteRequest(addr=0xac04, val=0x0955)
    if side=='center':
        SimpleWriteRequest(addr=0xac04, val=0x0eaa)

def slvs_output_strength(value=0x4,side='top'):
    if side=='top':
        SimpleWriteRequest(addr=0xcc05, val=value)
    if side=='bot':
        SimpleWriteRequest(addr=0x4c05, val=value)
    if side=='center':
        SimpleWriteRequest(addr=0xac05, val=value)

def enable_dac_out(ENABLE_DAC_OUT=True,side='top'):
    F_ENABLE_DAC_OUT = ENABLE_DAC_OUT << 12
    if side=='top':
        v = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xcc04, count=1)).data)
        v |= F_ENABLE_DAC_OUT
        SimpleWriteRequest(addr=0xcc04, val=v)
    if side=='bot':
        v = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x4c04, count=1)).data)
        v |= F_ENABLE_DAC_OUT
        SimpleWriteRequest(addr=0x4c04, val=v)
    if side=='center':
        v = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xac04, count=1)).data)
        v |= F_ENABLE_DAC_OUT
        SimpleWriteRequest(addr=0xac04, val=v)

#ADC sample
def ADC_Sample(OSR, wait, ):
    #start ADC sample
    SimpleWriteRequest(addr=0xA033, val=1)
    time.sleep(wait)
    adc_32_out=rpc.decode_S32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xA034, count=1)).data)
    return 0.6 + (1.2*adc_32_out)/((OSR+1)*OSR)

def ADC_externalSample(peripheralService):
    resp = peripheralSenseNow(rpc.StringList(items = [ 'carrier/adc/volt' ]))
    return resp.items[0].value.float_value

#Reverse bits if needed
def reverse_Bits(n, no_of_bits):
    result = 0
    for i in range(no_of_bits):
        result <<= 1
        result |= n & 1
        n >>= 1
    return result

# Handy function to configure DAC selection register
def setDacOut(selection,AEOC):
    R_ANA_DAC_OUT_SEL = 0xA01A
    dacOutReg = (0x7 & selection[0]) << 28
    dacOutReg |= (0x3F & selection[2]) << 22
    dacOutReg |= (0x7FF & ( selection[1] | AEOC << 4 )  ) << 11
    dacOutReg |= (0x7FF & ( selection[3] | AEOC << 4 )  ) << 0
    SimpleWriteRequest(addr=R_ANA_DAC_OUT_SEL, val=dacOutReg)

def PS_monitor_center(addr_13=0x0, addr_23=0x0, printVal=False, OSR=0):
    setDacOut((0x2, 0x0, addr_13, 0x0),0)
    V_13=ADC_Sample(OSR, 0)
    setDacOut((0x2, 0x0, addr_23, 0x0),0)
    V_23=ADC_Sample(OSR, 0)
    PS_mon=(V_23-V_13)*3
    if printVal:
        print ('%6x\t%3.3f\t%6x\t%3.3f\t%3.3f'%(addr_13,V_13,addr_23,V_23, PS_mon))
    return PS_mon

def Set_ADC_conf(clock_ref=2**6, osr=2**14):
    SimpleWriteRequest(addr=0xA030, val=clock_ref)
    SimpleWriteRequest(addr=0xA031, val=osr)
    OSR = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xA031, count=1)).data)
    return OSR


def Temperature(printVal=False, OSR=0,peripheralService=0):
    TEMP_ADJ=0
    setDacOut((0x2, 0x0, 0x2, 0x0),0)
    bg_temp=ADC_Sample(OSR, 0 )
    bg_temp_ext=ADC_externalSample(peripheralService)
    setDacOut((0x2, 0x0, 0x5, 0x0),0)
    bg_100mV=ADC_Sample(OSR, 0)
    bg_100mV_ext=ADC_externalSample(peripheralService)
    temp=330.7 - (529.6 * (bg_temp - bg_100mV)) + TEMP_ADJ
    temp_ext=330.7 - (529.6 * (bg_temp_ext - bg_100mV_ext)) + TEMP_ADJ
    if printVal:
        print ('TEMP: %3.3f\t%3.3f\t%3.3f\t'%(bg_temp,bg_100mV,temp))
        print ('TEMP_ext: %3.3f\t%3.3f\t%3.3f\t'%(bg_temp_ext,bg_100mV_ext,temp_ext))
    return temp
    # return bg_temp,bg_100mV

def decodeDLL(eoc_dll_read):
    return ( (eoc_dll_read>>5 & 0xF) | (eoc_dll_read<<3 & 0xF0))

def DLL_is_locked(eoc_dll_read):
    return eoc_dll_read & 0x1

def power_up_dll():
    SimpleWriteRequest(addr=0x8003, val= 1<<9)
    SimpleWriteRequest(addr=0x8003, val= 0)

def bypass_dll(bypass=True,code=0x0):
    bypass_dll = bypass&0x1
    bypass_dll |= (code<<1) & 0x1fe
    SimpleWriteRequest(addr=0x8003, val= bypass_dll )

def enable_dll_clk_col(Top=True, col=0, enable=True, ):
    reg_number=int(col/16)
    val= enable << col%16
    if Top:
        SimpleWriteRequest(addr=0x8080 + reg_number, val=val)
    else:
        SimpleWriteRequest(addr=0x8070 + reg_number, val=val)

def set_dll_lock(window=0, threshold=0x40):
    data=threshold&0xff
    data|=window<<8 &0x300
    SimpleWriteRequest(addr=0x8002, val= data)

def set_dll_clk(lock_threshold=1, toa_clk_edge=0, clk_dll_freq_sel=0x00, enable_toa=0, toa_bin_or_gray=1, bypass_center_pll=1, enable_cols=0):
    set_dll_lock(window=lock_threshold, threshold=0x40 )
    for n in range(0,14):
        if enable_cols:
            SimpleWriteRequest(addr=0x8070 + n, val=0xFFFF)
            SimpleWriteRequest(addr=0x8080 + n, val=0xFFFF)
        else:
            SimpleWriteRequest(addr=0x8070 + n, val=0x0000)
            SimpleWriteRequest(addr=0x8080 + n, val=0x0000)
    set_clock_generator_center(clk_dll_freq_sel=clk_dll_freq_sel, bypass_pll=bypass_center_pll,enable_clockgating=0 )
    SimpleWriteRequest(addr=0x8054, val= toa_clk_edge<<3 | toa_bin_or_gray << 1 | enable_toa )
    power_up_dll()

def set_clock_generator_center(clk_dll_freq_sel=0x0,bypass_pll=True,enable_clockgating=0):
    ck_gen=enable_clockgating&0x1
    ck_gen |= (bypass_pll<<1) & 0x02
    ck_gen |= (clk_dll_freq_sel<<2) & 0x1C
    SimpleWriteRequest(addr=0x8062, val=ck_gen)

def column_data_mask(top=False, col=0, mask=True):
    if mask and top:
        print("Double Column TOP %d masked"%col)
    if mask and not top:
        print("Double Column BOT %d masked"%col)
    if top:
        addr = 0xCD00 + int(col/16)
        val = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=addr, count=1)).data)
        val |= mask << col%16
    else:
        addr = 0x4D00 + int(col/16)
        val = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=addr, count=1)).data)
        val |= mask << col%16
    SimpleWriteRequest(addr=addr, val=val)

def unmask_all_column_data():
    for n in range(0,14):
        SimpleWriteRequest(addr=0xCD00 + n, val=0x0)
        SimpleWriteRequest(addr=0x4D00 + n, val=0x0)

def set_pll_settings():
    # pll_conf_top=0x3905fc0
    # pll_conf_bot=0x3905fc1
    # pll_conf_center=0x3905fc1
    # SimpleWrite(rpc.SimpleWriteRequest(addr=0xc300, val=pll_conf_top))
    # SimpleWrite(rpc.SimpleWriteRequest(addr=0x4300, val=pll_conf_bot))
    # SimpleWrite(rpc.SimpleWriteRequest(addr=0xa020, val=pll_conf_center))

    #PLL TOP
    set_pll_conf(res=0x7,
                 icp=0x5,
                 adj_cp=0x0,
                 div_2_ON=False,
                 en_pll=True,
                 cap_small=0x7,
                 cap_large=0xf,
                 rst_cntr_vdd=False,
                 adj_vco=0x0,
                 select_local_clk_ref_pll=1,
                 addr=0xc300)
    #PLL BOT
    set_pll_conf(res=0x7,
                 icp=0x5,
                 adj_cp=0x0,
                 div_2_ON=False,
                 en_pll=True,
                 cap_small=0x7,
                 cap_large=0xf,
                 rst_cntr_vdd=False,
                 adj_vco=0x0,
                 select_local_clk_ref_pll=1,
                 addr=0x4300)
    #PLL CENTER
    set_pll_conf(res=0x7,
                 icp=0x3,
                 adj_cp=0x0,
                 div_2_ON=False,
                 en_pll=True,
                 cap_small=0x7,
                 cap_large=0xf,
                 rst_cntr_vdd=False,
                 adj_vco=0x8,
                 select_local_clk_ref_pll=1,
                 addr=0xa020)


def set_pll_conf(res=0x7, icp=0x1, adj_cp=0x0, div_2_ON=False, en_pll=False, cap_small=0x7, cap_large=0xf, rst_cntr_vdd=False, adj_vco=0x0, select_local_clk_ref_pll=0, addr=0):

    pll_conf = select_local_clk_ref_pll &0x1
    pll_conf |= (adj_vco<<1) & 0x1e
    pll_conf |= (rst_cntr_vdd<<5) & 0x20
    pll_conf |= (cap_large<<6) & 0x3c0
    pll_conf |= (cap_small<<10) & 0x3c00
    pll_conf |= (en_pll<<14) & 0x4000
    pll_conf |= (div_2_ON<<15) & 0x8000
    pll_conf |= (adj_cp<<16) & 0xf0000
    pll_conf |= (icp<<20) & 0x700000
    pll_conf |= (res<<23) & 0x7800000
    SimpleWriteRequest(addr=addr, val=pll_conf)


def reset_periphery_plls():
    addrs=[0xc300, 0x4300, 0xa020]
    for addr in addrs:
        val_r = rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=addr, count=1)).data)
        val = 0xFFFF_FFDF & val_r | 0x1 << 5
        #print("Reset PLL 1: %x %x"%(addr,val))
        SimpleWriteRequest(addr=addr, val=val)
        val = 0xFFFF_FFDF & val_r
        #print("Reset PLL 0: %x %x"%(addr,val))
        SimpleWriteRequest(addr=addr, val=val)

def set_clocks_periphery_edges( top=False, enable_clockgating=0, dual_edge_clk=0, bypass_pll=1, clk_datapath_src=0x2, clk_datapath_en=1, clk_encoder_en=1):

    # set_pll_settings(service)

    ck_gen_conf = enable_clockgating & 0x1
    ck_gen_conf |= (dual_edge_clk<<1) & 0x2
    ck_gen_conf |= (bypass_pll<<2) & 0x4
    ck_gen_conf |= (clk_datapath_src<<3) & 0x38
    ck_gen_conf |= (clk_datapath_en<<6) & 0x40
    ck_gen_conf |= (clk_encoder_en<<10) & 0x400
    if top:
        SimpleWriteRequest(addr=0xc205, val=ck_gen_conf)
    else:
        SimpleWriteRequest(addr=0x4205, val=ck_gen_conf)
    return

def read_clock_status_edges(top=False):
    addr=[0x4205,0xc205]
    addr2=[0x4207,0xc207]
    top_f=["BOT","TOP"]
    val_r = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=addr[top], count=1)).data)
    dual_edge_clk = val_r >> 1 & 0x01
    bypass_pll = val_r >> 2 & 0x01
    clk_datapath_src = val_r >> 3 & 0x07
    clk_datapath_en = val_r >> 6 & 0x01
    clk_encoder_en = val_r >> 10 & 0x01
    if clk_datapath_src>= 0x5:
        clk_datapath_src= 0x4
    clk_datapath_freq=320/2**(clk_datapath_src-dual_edge_clk+bypass_pll*3)
    val_r = rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=addr2[top], count=1)).data)
    hig_BW_en = val_r >> 24 & 0x01
    clk_encoder_freq = clk_datapath_freq*2**hig_BW_en
    print("#############################################")
    print("%s DATAPATH CLK FREQ %dMHz GWT CLK FREQ %dMHz"%(top_f[top],clk_datapath_freq,clk_encoder_freq))
    return clk_datapath_freq

def T0_sync():
    SimpleWriteRequest(addr=0x8051, val=0x9)

def TP_start():
    SimpleWriteRequest(addr=0x8051, val=0x5)

def Shutter_open():
    SimpleWriteRequest(addr=0x8051, val=0x1)

def Datapath_Reset():
    SimpleWriteRequest(addr=0x8051, val=0xa)

def Disable_ReadOut():
    SimpleWriteRequest(addr=0x8051, val=0x4)

def Enable_ReadOut():
    SimpleWriteRequest(addr=0x8051, val=0x3)


def reset_matrix(reset_pixel_conf=True):
    matrix_conf = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x8000, count=1)).data)
    if reset_pixel_conf:
        SimpleWriteRequest(addr=0x8000, val=matrix_conf | 1<<10)
    else:
        SimpleWriteRequest(addr=0x8000, val=matrix_conf & ~(1<<10))
    SimpleWriteRequest(addr=0x8051, val=0x6)

def analog_periphery_reg(select_VCO_control=0, select_Polarity_or_LogGainEn=0, R1_BandGap=0x7, R3_BandGap=0x0 ):
    reg = R3_BandGap & 0x7
    reg |= (R1_BandGap << 3 ) &0x38
    reg |= (select_Polarity_or_LogGainEn << 6 ) &0x40
    reg |= (select_VCO_control << 7 ) &0x80
    SimpleWriteRequest(addr=0xa01b, val=reg)


def data_decode_sc(val):
    data = (val & 0xFF) << (64-8)
    data |= (val & 0xFF00) << (64-8*3)
    data |= (val & 0xFF0000) << (64-8*5)
    data |= (val & 0xFF0000) << (64-8*5)
    data |= (val & 0xFF000000) << (64-8*7)
    data |= (val & 0xFF00000000) >> (8*1)
    data |= (val & 0xFF0000000000) >> (8*3)
    data |= (val & 0xFF000000000000) >> (8*5)
    data |= (val & 0xFF00000000000000) >> (8*7)
    return data

def status_monitor_config(side, signal_select=0, heartbeat_period_shift=16, enable_heartbeat=0,
                          enable_ctrl_data_test=0, enable_global_time_reset=1, enable_global_time=False, enable_status_proc=0):
    status_reg = enable_status_proc & 0x001
    status_reg |= (enable_global_time << 1 ) &0x002
    status_reg |= (enable_global_time_reset << 2 ) &0x004
    status_reg |= (enable_ctrl_data_test << 3 ) &0x008
    status_reg |= (enable_heartbeat << 4 ) &0x010
    status_reg |= (heartbeat_period_shift << 5 ) &0x3e0
    status_reg |= (signal_select << 10 ) &0xc00
    if side=='top':
        SimpleWriteRequest(addr=0xcc02, val=status_reg)
    if side=='bot':
        SimpleWriteRequest(addr=0x4c02, val=status_reg)

def configure_TP(TP_number=0, TP_period_on=0, TP_period_off=0,tp_phase=0, tp_enable=False ,link_shutter_and_tp=False,
                 select_digital_tp=False , shutter2tp_lat=16):
    SimpleWriteRequest(addr=0x8057, val=TP_number)
    val=tp_time(TP_period_on)
    SimpleWriteRequest(addr=0x8058, val=val)
    val=tp_time(TP_period_off)
    SimpleWriteRequest(addr=0x8059, val=val)
    tp_conf =  shutter2tp_lat & 0x7F
    tp_conf |= (select_digital_tp << 7) & 0x80
    tp_conf |= (link_shutter_and_tp << 8) & 0x100
    tp_conf |= (tp_enable << 9) & 0x200
    tp_conf |= (tp_phase << 10) & 0x3C00
    SimpleWriteRequest(addr=0x8050, val=tp_conf)

def readout_control(Top=True, readout_enable=0, select_routing_table=0, nchannels=0x0, frame_readout_trigger=0, start_frame_readout=0,
                    read_packets_via_slow_ctrl=1, crw_mode=0, readout_mode=0x1):
    readout_control = readout_mode & 0x3
    readout_control |= (crw_mode <<2 ) & 0x4
    readout_control |= (read_packets_via_slow_ctrl <<3 ) & 0x8
    readout_control |= (start_frame_readout <<4 ) & 0x10
    readout_control |= (frame_readout_trigger <<5 ) & 0x20
    readout_control |= (nchannels <<6 ) & 0xC0
    readout_control |= (select_routing_table <<8 ) & 0x100
    readout_control |= (readout_enable <<9 ) & 0x200
    if Top:
        SimpleWriteRequest(addr=0xc204, val=readout_control)
    else:
        SimpleWriteRequest(addr=0x4204, val=readout_control)

def CTPR_enable(enable_top=0x0001, enable_bot=0x00001):
    for add in range(0,14):
        SimpleWriteRequest(addr=0x8030+add, val=enable_bot)
        SimpleWriteRequest(addr=0x8040+add, val=enable_top)

def CTPR_enable_col(Top=True, eoc=0, enable=True):
    reg_number=int(eoc/16)
    val= enable << eoc%16
    if Top:
        reg=0x8040 + reg_number
        read_reg=rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=reg, count=1)).data)
        if enable:
            val |= read_reg
        else:
            val &= read_reg
        SimpleWriteRequest(addr=reg, val=val)
    else:
        reg=0x8030 + reg_number
        read_reg=rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=reg, count=1)).data)
        if enable:
            val |= read_reg
        else:
            val &= read_reg
        SimpleWriteRequest(addr=reg, val=val)

def mask_col(Top=True, eoc=0, mask=True):
    reg_number=int(eoc/16)
    val= mask << eoc%16
    if Top:
        reg=0xcd00 + reg_number
        read_reg=rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=reg, count=1)).data)
        if mask:
            val |= read_reg
        else:
            val &= read_reg
        SimpleWriteRequest(addr=reg, val=val)
    else:
        reg=0x4d00 + reg_number
        read_reg=rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=reg, count=1)).data)
        if mask:
            val |= read_reg
        else:
            val &= read_reg
        SimpleWriteRequest(addr=reg, val=val)

def decode_packet(packet, mode, gray, ratio_VCO_CKDLL=16):
    Top = (packet >> 63) & 0x1
    EoC = (packet >> 55) & 0xff
    if EoC > 0xDF:
        out=['CONTROL', Top, EoC, packet & 0x7f_ffff_ffff_ffff ]
    else:
        addr=  (packet>>46) & 0x3ffff
        if mode == 0x0:   #TOA-TOT DD
            pileup = packet & 0x1
            tot = (packet>>1) & 0x7ff
            ftoa_fall = (packet >> 12) & 0x1f
            ftoa_rise = (packet >> 17) & 0x1f
            uftoa_stop = decode_uftoa((packet >> 22) & 0xf)
            uftoa_start = decode_uftoa((packet >> 26) & 0xf)
            toa = (packet >> 30) & 0xffff
            if gray:
                toa = inversegrayCode(toa)
            pixel = (packet >> 46) & 0x7
            Spixel = (packet >> 49) & 0x3
            SpGroup = (packet >> 51) & 0xf
            tot_hd=decode_tot(ftoa_rise, ftoa_fall, uftoa_start, uftoa_stop, tot, ratio_VCO_CKDLL)
            toa_hd=decode_toa(toa,uftoa_start, uftoa_stop, ftoa_rise, ratio_VCO_CKDLL)
            toa_clkdll_c=toa_clkdll_correction(spgroup_addr=SpGroup)
            out = ['DATA TOA-TOT', Top, addr, EoC, SpGroup, Spixel*8+pixel,     #5
            toa,uftoa_start, uftoa_stop, ftoa_rise, ftoa_fall, tot, pileup,     #12
            toa_hd,tot_hd,toa_clkdll_c,toa_hd-toa_clkdll_c,0, Spixel, pixel]    #19
        if mode == 0x1: #8-b FB
            out = ['DATA PC8b', packet ]
        if mode == 0x2: #16-b FB
            out = ['DATA PC16b', packet ]
        if mode == 0x3: #24-b DD
            out = ['DATA PC24b', Top, addr, packet & 0xffffff ]
    return out

def decode_tot(ftoa_rise, ftoa_fall, uftoa_start, uftoa_stop, tot, ratio_VCO_CKDLL):
    #Decode TOT
    if tot==0 and (ftoa_fall > ftoa_rise):  #Noticed that at TOT=0 I can get negative pulses...
        ftoa_fall=ftoa_rise-1
    # return (tot + (ftoa_rise - (uftoa_start-uftoa_stop)/8.)/(ratio_VCO_CKDLL) - ftoa_fall/ratio_VCO_CKDLL)
    return (tot + (ftoa_rise - ftoa_fall)/ratio_VCO_CKDLL)

def decode_toa(toa, uftoa_start, uftoa_stop, ftoa_rise, ratio_VCO_CKDLL):
    #Decode TOA
    return (toa - (ftoa_rise - (uftoa_start-uftoa_stop)/8.)/ratio_VCO_CKDLL)

def toa_clkdll_correction(spgroup_addr=0):
    #Corrects latency delay due to DDLL clock distribution
    clk_dll_step=1/32
    return (15-spgroup_addr)*clk_dll_step

def decode_uftoa(uftoa):
    #Thermometer decoding of UFTOA
    uftoa_list = [15, 14, 12, 8, 0, 1, 3, 7]
    if uftoa not in uftoa_list:
        val=0
    else:
        val=uftoa_list.index(uftoa)
    return val

def inversegrayCode(n):
    inv = 0
    # Taking xor until
    # n becomes zero
    while(n):
        inv = inv ^ n
        n = n >> 1
    return inv

def sequencer_reset(addr,reset_FE,duration,num_of_banks,cols_per_bank):
    reg = cols_per_bank & 0x7
    reg |= (num_of_banks << 3) & 0x38
    reg |= (duration << 6) & 0x1C0
    reg |= (reset_FE << 9) & 0x200
    SimpleWriteRequest(addr=0x8060, val=reg)

def sequencer(addr,duration,num_of_banks,cols_per_bank):
    reg = cols_per_bank & 0x7
    reg |= (num_of_banks << 3) & 0x38
    reg |= (duration << 6) & 0x1C0
    SimpleWriteRequest(addr=addr, val=reg)

def configure_links(top=False,channels=0x01, reverse_bits=0, speed_div_log2=0):
    val = speed_div_log2 & 0xF
    val |= (reverse_bits << 4) & 0x10
    val |= (channels << 5) & 0x1Fe0
    if top:
        SimpleWriteRequest(addr=0xcc01, val=val)
    else:
        SimpleWriteRequest(addr=0x4c01, val=val)
    return

def reset_gwt_digital_analog (top=False, channels=0x01):
    #Reset GWT (Resets RN_dig and RN_ana_core)
    #Resets first selected channels to 0 -> to 1
    if top:
        val_r = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xcc01, count=1)).data)
        val = val_r & 0x1F
        # print ("Reset GWT ON %x"%val)
        SimpleWriteRequest(addr=0xcc01, val=val)
        val |= channels << 5 & 0x1FE0
        # print ("Reset GWT OFF %x"%val)
        SimpleWriteRequest(addr=0xcc01, val=val)
    else:
        val_r = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x4c01, count=1)).data)
        val = val_r & 0x1F
        SimpleWriteRequest(addr=0x4c01, val=val)
        val |= channels << 5 & 0x1FE0
        SimpleWriteRequest(addr=0x4c01, val=val)

def reset_gwt_fifo(top=False, channels=0x01):
    #Reset GWT FIFOs (RN_fifo)
    #Resets first selected channels to 0 -> to 1
    if top:
        val_r = rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xc209, count=1)).data)
        val = val_r & 0xF807_FFFF
        # print ("Reset GWT FIFO ON %x"%val)
        SimpleWriteRequest(addr=0xc209, val=val)
        val |= channels << 19 & 0x07F80000
        # print ("Reset GWT FIFO OFF %x"%val)
        SimpleWriteRequest(addr=0xc209, val=val)
    else:
        val=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x4209, count=1)).data)
        val |= 0x00 << 19 & 0x07F80000
        SimpleWriteRequest(addr=0x4209, val=val)
        val |= channels << 19 & 0x07F80000
        SimpleWriteRequest(addr=0x4209, val=val)

def reset_gwt_digital(top=False, channels=0x01):
    reset_gwt_digital_analog(top=top, channels=channels)
    reset_gwt_fifo(top=top, channels=channels)

def enable_GWT(top=False, channels=0x01, high_BW_en=0, start_up_en=0x01, enable_cc_pll=True):
    val=0
    if enable_cc_pll:
        val = channels        # enables clock_cleaing_pll
    val |= channels << 8 & 0x0000_FF00  # enables GWT link
    val |= start_up_en << 16  & 0x00FF_0000 # Start_up enable
    val |= high_BW_en << 24  & 0x0100_0000 # high_BW_en enable
    if top:
        SimpleWriteRequest(addr=0xc207, val=val)
    else:
        SimpleWriteRequest(addr=0x4207, val=val)
    return

def prbs_pattern(top=False, prbs_on=False, channels=0x01, prbs_mode=0x1):
    #Sets all active channels with same PRBS test pattern
    if (prbs_mode >= 0x1 and prbs_mode <=0x5 and prbs_on):
        val = channels & 0x0000_00FF
        for i in range(0,8):
            if (channels & 0x01 << i):
                val |= prbs_mode << (8 + i*3) & 0x7 << (8 + i*3)
    else:
        val = 0x0
    if top:
        SimpleWriteRequest(addr=0xcb02, val=val)
    else:
        SimpleWriteRequest(addr=0x4b02, val=val)
    return

def reset_gwt_PLL_analog(top=False, channels=0x01, wait=0.0):
    #Resets analog GWT PLL
    if top:
        val_r=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xc208, count=1)).data)
        val = (val_r & 0xFFFF_FF00) | 0xFF
        SimpleWriteRequest(addr=0xc208, val=val)
        time.sleep(wait)
        val = (val_r & 0xFFFF_FF00) | ~channels & 0xFF
        SimpleWriteRequest(addr=0xc208, val=val)
    else:
        val_r=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x4208, count=1)).data)
        val = (val_r & 0xFFFF_FF00) | 0xFF
        SimpleWriteRequest(addr=0x4208, val=val)
        time.sleep(wait)
        val = (val_r & 0xFFFF_FF00) | ~channels & 0xFF
        SimpleWriteRequest(addr=0x4208, val=val)

def reset_gwt_DLL_analog(top=False, channels=0x01, wait=0.0):
    #Resets analog GWT DLL
    if top:
        val_r=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xc209, count=1)).data)
        val = (val_r & 0xFFF8_07FF) | (0xFF << 11)
        SimpleWriteRequest(addr=0xc209, val=val)
        #print ("RESET DLL ANALOG ON %x" %val)
        time.sleep(wait)
        val = (val_r & 0xFFF8_07FF) | (~channels << 11) & 0x7F800
        SimpleWriteRequest(addr=0xc209, val=val)
        #print ("RESET DLL ANALOG OFF %x" %val)
    else:
        val_r=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x4209, count=1)).data)
        val = (val_r & 0xFFF8_07FF) | (0xFF << 11)
        SimpleWriteRequest(addr=0x4209, val=val)
        time.sleep(wait)
        val = (val_r & 0xFFF8_07FF) | (~channels << 11) & 0x7F800
        SimpleWriteRequest(addr=0x4209, val=val)
    return


def start_up_links(top=True, channels=0x01, high_BW_en=1, enable_cc_pll=True, speed_div_log2=0x0 ):
    configure_links(top=top,  channels=channels, reverse_bits=0, speed_div_log2=speed_div_log2)
    reset_gwt_digital(top=top, channels=channels)
    enable_GWT(top=top, channels=channels, high_BW_en=high_BW_en, start_up_en=0x0, enable_cc_pll=enable_cc_pll)
    enable_GWT(top=top, channels=channels, high_BW_en=high_BW_en, start_up_en=channels,enable_cc_pll=enable_cc_pll)
    reset_gwt_digital(top=top, channels=channels)
    reset_gwt_PLL_analog(top=top, channels=channels)
    reset_gwt_DLL_analog(top=top, channels=channels)

    print("#############################################")
    if top:
        print('LINKS TOP %s STARTED @%d Mbps'%(bin(channels), linkspeed(speed_div_log2, high_BW_en) ))
    else:
        print('LINKS BOT %s STARTED @%d Mbps'%(bin(channels), linkspeed(speed_div_log2, high_BW_en) ))
    print("#############################################")
    return

def linkspeed(speed_div_log2, high_BW_en):
    return 2**(9-speed_div_log2 + high_BW_en)*10

def router8x8(Top=True, channels=0x01 ):
    val = channels<<8 | channels
    if Top:
        for i in range(0,4):
            SimpleWriteRequest(addr=0xc000 + i, val=val)
    else:
        for i in range(0,4):
            SimpleWriteRequest(addr=0x4000 + i, val=val)


def configure_matrix(low_gain_mode_bit=0, log_gain_enable=0,
                     polarity=1, reset_config=0, periodic_shutter =0,
                     shutter_mode=0, shutter_select=0, enable_tdc=0, op_mode=0x0):
    matrix_conf = op_mode & 0x3
    matrix_conf |= (enable_tdc <<2) & 0x4
    matrix_conf |= (shutter_select <<3) & 0x8
    matrix_conf |= (shutter_mode <<7) & 0x80
    matrix_conf |= (periodic_shutter <<8) & 0x100
    matrix_conf |= (polarity <<11) & 0x800
    matrix_conf |= (log_gain_enable <<12) & 0x1000
    matrix_conf |= (low_gain_mode_bit <<13) & 0x2000

    SimpleWriteRequest(addr=0x8000, val=matrix_conf)
    return

def shutter_on(shift_duration=0, duration=0):
    shutter_on = duration & 0x7FF
    shutter_on |= (shift_duration << 11) & 0xF800

    SimpleWriteRequest(addr=0x8055, val=shutter_on)
    return

def shutter_off(shift_duration=0, duration=0):
    shutter_on = duration & 0x7FF
    shutter_on |= (shift_duration << 11) & 0xF800

    SimpleWriteRequest(addr=0x8056, val=shutter_on)
    return

def pixel_conf(dac_bits=0x0, power_enable=1, tp_enable=0, mask_bit=0):
    conf = dac_bits & 0x1F
    conf |= power_enable<<5 &0x20
    conf |= tp_enable<<6 &0x40
    conf |= mask_bit<<7 &0x80
    return conf

def PixelGroup(Top=True, EoC=0x0, data=np.zeros(shape=(32,1), dtype=np.uint8)):
    if Top:
        SimpleWriteRequest(addr=0xe100 + SpGroup + EoC*16, data=data, count=1)
    else:
        SimpleWriteRequest(addr=0x6100 + SpGroup + EoC*16, data=data, count=1)

def PixelConfig(Top=True, EoC=0x0, SpGroup=0, data=np.zeros(shape=(32*16,1), dtype=np.uint8)):
    if Top:
        SimpleWriteRequest(addr=0xe000 + EoC, data=data, count=1)
    else:
        SimpleWriteRequest(addr=0x6000 + EoC, data=data, count=1)


def save_IDACs(fbase,DAC_I):
    data=np.zeros(len(DAC_I), dtype={'names':('dac_name', 'dac_addr', 'dac_code'),
                                     'formats':('U20', 'i4', 'i4')})
    dac_name=[]
    dac_addr=[]
    dac_code=[]
    for i in range(0, len(DAC_I)):
        dac_name.append(DAC_I[i][3])
        dac_addr.append(DAC_I[i][2])
        dac_code.append(rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=DAC_I[i][2], count=1)).data))

    data['dac_name']=dac_name
    data['dac_addr']=dac_addr
    data['dac_code']=dac_code
    np.savetxt(fbase+'dacs_i.dat', data, delimiter='\t', fmt='%s\t%d\t%d\t')

def save_VDACs(fbase, DAC_VB):
    data=np.zeros(len(DAC_VB), dtype={'names':('dac_name', 'dac_addr', 'dac_code', 'vgain_dac_addr', 'vgain_dac_code'),
                                     'formats':('U20', 'i4', 'i4', 'i4', 'i4')})
    dac_name=[]
    dac_addr=[]
    dac_code=[]
    vgain_dac_addr=[]
    vgain_dac_code=[]
    for i in range(0, len(DAC_VB)):
        dac_name.append(DAC_VB[i][3])
        dac_addr.append(DAC_VB[i][2])
        val = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=DAC_VB[i][2], count=1)).data)
        if (DAC_VB[i][6]):
            val=reverse_Bits(val,DAC_VB[i][4])
        dac_code.append(val)
        vgain_dac_addr.append(DAC_VB[i][8])
        val = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=DAC_VB[i][8], count=1)).data)
        if (DAC_VB[i][7]):
            val=reverse_Bits(val,4)
        vgain_dac_code.append(val)
    data['dac_name']=dac_name
    data['dac_addr']=dac_addr
    print(dac_code)
    data['dac_code']=dac_code
    data['vgain_dac_addr']=vgain_dac_addr
    data['vgain_dac_code']=vgain_dac_code
    np.savetxt(fbase+'dacs_v.dat', data, delimiter='\t', fmt='%s\t%d\t%d\t%d\t%d\t')

def save_DACs(fbase,DAC_I, DAC_VB, DAC_VT):
    dac_np=np.array(shape=(len(DAC_I),2), dtype='int')
    for i in range(0, len(DAC_I)):
        dac_np[i][1]=DAC_I[i][2]
        dac_np[i][2] = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=DAC_I[i][2], count=1)).data)
    np.savetxt(fbase+'dacs_i.dat', dac_np, delimiter='\t', fmt='%d')

    dac_np=np.zeros(shape=(len(DAC_VB),4), dtype='int')
    for i in range(0, len(DAC_VB)):
        dac_np[i][1]=DAC_VB[i][2]
        val = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=DAC_VB[i][2], count=1)).data)
        if (DAC_VB[i][6]):
            val = reverse_Bits(val,DAC_VB[i][4])
        dac_np[i][2]=val

        dac_np[i][3]=DAC_VB[i][8]
        val = rpc.decode_u16(ReadReg(rpc.ReadRegRequest(idx=0, addr=DAC_VB[i][8], count=1)).data)
        if (DAC_VB[i][7]):
            val = reverse_Bits(val,4)
        dac_np[i][4] =val
    np.savetxt(fbase+'dacs_v.dat', dac_np, delimiter='\t', fmt='%d')

def load_DACs(fbase, DAC_I, DAC_VB, DAC_VT):
    dac_np=np.loadtxt(fbase+'dacs_i.dat', delimiter='\t', dtype='str,int,int' )
    # print(dac_np, len(dac_np))
    for i in range(0, len(dac_np)):
        DAC_I[i][5]=int(dac_np[i][2])
        print(DAC_I[i])
        # print(dac_np[i])
        dacs.Set_DAC(DAC=DAC_I[i], val=DAC_I[i][5], sampleADC=False, OSR=0, print_enable=True)
    dac_np=np.loadtxt(fbase+'dacs_v.dat', delimiter='\t',dtype='str,int,int,int,int')
    # print(dac_np, len(dac_np))
    for i in range(0, len(dac_np)):
        DAC_VB[i][5]=int(dac_np[i][2])
        DAC_VT[i][5]=DAC_VB[i][5]
        DAC_VB[i][9]=int(dac_np[i][4])
        DAC_VT[i][9]=DAC_VB[i][9]
        # print(DAC_VB[i],DAC_VT[i] )
        dacs.Set_DAC(DAC=DAC_VB[i], val=DAC_VB[i][5], sampleADC=False, OSR=0, print_enable=True)

def set_PC24b_Threshold(threshold):
    WriteReg(rpc.WriteRegRequest(idx=0, addr=0x8001, data=rpc.encode_u16(threshold), count=1))

def read_fuses(top=True):
    if top:
        SimpleWriteRequest(addr=0xcd20, val=0x1)
        efuse_out=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xcd21, count=1)).data)
        print("#############################################")
        print('TOP ID:%08x -> %s'%(efuse_out,decode_chipID(efuse_out)))
        print("#############################################")
    else:
        SimpleWriteRequest(addr=0x4d20, val=0x1)
        efuse_out=rpc.decode_u32(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x4d21, count=1)).data)
        print("#############################################")
        print('BOT ID:%08x -> %s'%(efuse_out,decode_chipID(efuse_out)))
        print("#############################################")

def burn_fuse(top=True, fuse_val=0):
    if top:
        SimpleWriteRequest(addr=0xcc07, val=fuse_val)
        SimpleWriteRequest(addr=0x4c07, val=0x0)
        SimpleWriteRequest(addr=0xcd20, val=0x2)
    else:
        SimpleWriteRequest(addr=0xcc07, val=0x0)
        SimpleWriteRequest(addr=0x4c07, val=fuse_val)
        SimpleWriteRequest(addr=0x4d20, val=0x2)

def decode_chipID(val=0x0):
    X_map=["noFused","A","B","C","D","E","F","G","H","I","J","K"]
    Y=val & 0xF
    Xv=val>>4 & 0xF
    if Xv > 11:
        X="noFused"
    else:
        X=X_map[Xv]
    W=val>>8 & 0xFFF
    MOD=val>>20 & 0x3
    if MOD==0x1:
        Y=val>>22 & 0xF
    if MOD==0x2:
        Xv=val>>22 & 0xF
        if Xv > 11:
            X="noFused"
        else:
            X=X_map[Xv]
    if MOD==0x3:
        W=val>>22 & 0x3FF
    return ("W%d_%s%d"%(W,X,Y))

def set_frame_base_wait(top=False, wait_time_s=0.0001):
    val=int(wait_time_s/(25*10**-9))
    if val>=2**32:
        val=2**32-1
    if top:
        SimpleWriteRequest(addr=0xc202, val=val)
    else:
        SimpleWriteRequest(addr=0x4202, val=val)

def tp_time(time):
    val=int(time/(25*10**-9))
    if val>=2**16:
        val=2**16-1
    return val

def crw_wait_time(time):
    val=int(time/(25*10**-9))
    if val>=2**16:
        val=2**16-1
    return val


def shutter_time(a,b):
    return (2**a)*(25*10**-9)*b

def shutter_b(time,a):
    return math.floor(time/((25*10**-9)*(2**a)))

def shutter_a(time,b):
    return math.floor(math.log2(time/((25*10**-9)*b)))

def shutter_length(dir, time):
    b=1000
    a=shutter_a(time,b)
    while (a<0):
        b -= 1
        a=shutter_a(time,b)
    b=shutter_b(time,a)
    if b>2047:
        b=2047
    if a>31:
        a=31
    print('Shutter %s time:'%dir,a,b,shutter_time(a,b))
    return (a,b)

def shutter_on_time(time):
    a,b=shutter_length("ON ",time)
    shutter_on(shift_duration=a, duration=b)

def shutter_off_time(time):
    a,b=shutter_length("OFF",time)
    shutter_off(shift_duration=a, duration=b)

def read_spgroup(top=True, dcol=0):
    str=["BOT","TOP"]
    if top:
        data = rpc.decode_u384(ReadReg(rpc.ReadRegRequest(idx=0, addr=0xf000+dcol, count=1)).data)
    else:
        data = rpc.decode_u384(ReadReg(rpc.ReadRegRequest(idx=0, addr=0x7000+dcol, count=1)).data)
    # for d in data:
    print("%s %x"%(str[top],data))

def write_spgroup(top=True, dcol=0, val=0x0):
    str=["TOP","BOT"]
    if top:
        WriteReg(rpc.WriteRegRequest(idx=0, addr=0xf000+dcol, data=val, count=1))
    else:
        WriteReg(rpc.WriteRegRequest(idx=0, addr=0x7000+dcol, data=val, count=1))
