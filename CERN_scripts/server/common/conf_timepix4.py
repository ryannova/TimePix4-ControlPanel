
import grpc
import rpc
import matplotlib.pyplot as plt
import numpy as np
import time
import dacs
import math
import api
import matrix as mat

def conf_timepix4(fbase=0,
                  SIDE='bot',
                  OSR_CLOCK_REF=2**4,
                  OSR_OSR=2**15,
                  POWER_MODE=2,  #0:Nominal, 1:Low, 2:OFF
                  GRAY_COUNTER=True,
                  BYPASS_CENTER=True,
                  BYPASS_DAC_SETTING=False,
                  FAST_RESET=False,
                  POLARITY=True,
                  LOW_GAIN=False,
                  LOG_GAIN=False,
                  ENABLE_STATUS_PROC=True,
                  HEARTBEAT_ENABLE=True,
                  ENABLE_TOA=True,
                  ENABLE_TDC=True,
                  ENABLE_DLL_COLS=True,
                  CHANNELS=0x01,
                  READ_OUT_SLOW_CONTROL=True,
                  PRBS_ON=True,
                  PRBS_MODE=0x04,
                  SPEED_DIV_LOG2=0x0,
                  ENABLE_CC_PLL=True,
                  MODE_10GB=False,
                  TP_ON=False,
                  TP_DIGITAL=False,
                  NUM_TP=10,
                  TP_TIME_ON=0.00001,
                  TP_TIME_OFF=0.00002,
                  OP_MODE=0x1,
                  PC24b_THRESHOLD=0x0001,
                  SHUTTER_TIME_ON=0.1,
                  SHUTTER_TIME_OFF=0.01,
                  READOUT_MODE=0x1,
                  CRW_WAIT_S=0.0001,
                  service=0,
                  peripheral=0,
                  control=0):

    #Resets Timepix4
    # control.ResetPixelChips(rpc.EMPTY)
    api.set_conf_io(side=SIDE,service=service)

    #Center SLVS OFF
    api.slvs_output_strength(value=0x0,side='center',service=service)
    #Edges SLVS
    api.slvs_output_strength(value=0x0,side='top',service=service)
    api.slvs_output_strength(value=0x7,side='bot',service=service)

    api.set_pll_settings(service=service)
    api.reset_periphery_plls(service=service)

    api.set_clocks_periphery_edges(top=True, enable_clockgating=0, dual_edge_clk=1, bypass_pll=0, clk_datapath_src=0x2, clk_datapath_en=1, clk_encoder_en=1, service=service)
    api.set_clocks_periphery_edges(top=False, enable_clockgating=0, dual_edge_clk=1, bypass_pll=0, clk_datapath_src=0x2, clk_datapath_en=1, clk_encoder_en=1, service=service)
    api.set_dll_clk(lock_threshold=1, toa_clk_edge=1 , clk_dll_freq_sel=0x0, enable_toa=ENABLE_TOA, toa_bin_or_gray=GRAY_COUNTER, bypass_center_pll=BYPASS_CENTER,
        enable_cols=ENABLE_DLL_COLS, service=service)

    clk_datapath_freq=api.read_clock_status_edges(top=True, service=service)
    api.set_frame_base_wait(top=True,  wait_time_s=CRW_WAIT_S*(clk_datapath_freq/40), service=service)
    clk_datapath_freq=api.read_clock_status_edges(top=False, service=service)
    api.set_frame_base_wait(top=False, wait_time_s=CRW_WAIT_S*(clk_datapath_freq/40), service=service)

    DAC_I = []
    DAC_VB = []
    DAC_VT = []
    AEOC =[]
    dacs.AEOC_DACs(AEOC)
    dacs.DACs(DAC_I, DAC_VB, DAC_VT)
    OSR=OSR_OSR
    # api.load_DACs(fbase, DAC_I, DAC_VB, DAC_VT, service)
    dacs.DACs_set_default(DAC_I=DAC_I, DAC_VB=DAC_VB, DAC_VT=DAC_VT,PowerMode=POWER_MODE,service=service)
    # api.load_DACs(fbase, DAC_I, DAC_VB, DAC_VT, service)
    if not (BYPASS_DAC_SETTING or FAST_RESET):
        api.analog_periphery_reg(R1_BandGap=0x2, R3_BandGap=0x5,  service=service)
        # dacs.DACs_set_default(DAC_I=DAC_I, DAC_VB=DAC_VB, DAC_VT=DAC_VT,LowPower=LOW_POWER,service=service)
        OSR=api.Set_ADC_conf(clock_ref=OSR_CLOCK_REF, osr=OSR_OSR, service=service)
        # api.load_DACs(fbase, DAC_I, DAC_VB, DAC_VT, service)

        dacs.Read_DACs(DAC_I, DAC_VB, DAC_VT, OSR, service)
        dacs.SupplyCenter(OSR, service)

        dacs.SupplyCenter(OSR, service)
        temp=api.Temperature(OSR=OSR, printVal=True, service=service, peripheralService=peripheral)

    if not FAST_RESET:
        api.router8x8(Top=True, channels=CHANNELS,service=service )
        api.router8x8(Top=False, channels=CHANNELS,service=service )
        api.readout_control(Top=True, readout_enable=False,readout_mode=READOUT_MODE, read_packets_via_slow_ctrl=READ_OUT_SLOW_CONTROL, service=service)
        api.readout_control(Top=False, readout_enable=False,readout_mode=READOUT_MODE, read_packets_via_slow_ctrl=READ_OUT_SLOW_CONTROL, service=service)

        api.prbs_pattern(top=True, channels=CHANNELS, prbs_on=PRBS_ON, prbs_mode=PRBS_MODE, service=service)
        api.prbs_pattern(top=False, channels=CHANNELS, prbs_on=PRBS_ON, prbs_mode=PRBS_MODE , service=service)
        api.start_up_links(top=True, channels=CHANNELS, high_BW_en=MODE_10GB, enable_cc_pll= ENABLE_CC_PLL, speed_div_log2=SPEED_DIV_LOG2,  service=service)
        api.start_up_links(top=False, channels=CHANNELS, high_BW_en=MODE_10GB, enable_cc_pll= ENABLE_CC_PLL, speed_div_log2=SPEED_DIV_LOG2, service=service)


        #Shutter sequencer
        api.sequencer(addr=0x8061,num_of_banks=0x5,cols_per_bank=0x4,duration=0x0,service=service)
        # api.sequencer(addr=0x8061,num_of_banks=0x0,cols_per_bank=0x0,duration=0x0,service=service)
        #CRW_TOP sequencer
        api.sequencer(addr=0xC206,num_of_banks=0x5,cols_per_bank=0x4,duration=0x0,service=service)

        #CRW_BOT sequencer
        # api.sequencer(addr=0x4206,num_of_banks=0x5,cols_per_bank=0x0,duration=0x4,service=service)
        api.sequencer(addr=0x4206,num_of_banks=0x5,cols_per_bank=0x4,duration=0x0,service=service)

        #reset sequence
        api.sequencer_reset(addr=0x8060,reset_FE=1,num_of_banks=0x0,cols_per_bank=0x0,duration=0x0,service=service)

        api.reset_matrix(reset_pixel_conf=True, service=service)

        api.status_monitor_config(side='top', signal_select=0, heartbeat_period_shift=22, enable_heartbeat=HEARTBEAT_ENABLE, enable_ctrl_data_test=False,
                                  enable_global_time_reset=True,
                                  enable_global_time=True,enable_status_proc=ENABLE_STATUS_PROC, service=service )
        api.status_monitor_config(side='bot', signal_select=1, heartbeat_period_shift=22, enable_heartbeat=HEARTBEAT_ENABLE, enable_ctrl_data_test=False,
                                  enable_global_time_reset=True,
                                  enable_global_time=True, enable_status_proc=ENABLE_STATUS_PROC, service=service )

        api.CTPR_enable(enable_top=0x0000, enable_bot=0x0000, service=service)

        api.set_PC24b_Threshold(threshold=PC24b_THRESHOLD,service=service )

        api.Datapath_Reset(service=service)
        api.configure_TP(TP_number=NUM_TP, TP_period_on=TP_TIME_ON, TP_period_off=TP_TIME_OFF, tp_phase=0x1,
                     tp_enable=TP_ON ,link_shutter_and_tp=TP_ON, select_digital_tp=TP_DIGITAL , shutter2tp_lat=0x7F, service=service )

        api.readout_control(Top=True, readout_enable=True, readout_mode=READOUT_MODE, read_packets_via_slow_ctrl=READ_OUT_SLOW_CONTROL, service=service)
        api.readout_control(Top=False, readout_enable=True, readout_mode=READOUT_MODE, read_packets_via_slow_ctrl=READ_OUT_SLOW_CONTROL, service=service)

        api.unmask_all_column_data(service=service)

        api.read_fuses(top=True, service=service)
        api.read_fuses(top=False, service=service)


    api.shutter_on_time(time=SHUTTER_TIME_ON,service=service)
    api.shutter_off_time(time=SHUTTER_TIME_OFF,service=service)

    api.analog_periphery_reg(select_VCO_control=0, select_Polarity_or_LogGainEn=POLARITY,  service=service)
    api.configure_matrix(polarity=POLARITY, low_gain_mode_bit=LOW_GAIN, log_gain_enable=LOG_GAIN, shutter_mode=1, periodic_shutter=0,
                         shutter_select=1, enable_tdc=ENABLE_TDC, op_mode=OP_MODE, service=service)


    # dacs.Read_AEOC_vals(AEOC, 0, 1, OSR, service)

    return (DAC_I, DAC_VB, DAC_VT, AEOC, OSR)

def conf_threshold(LOW_GAIN=False,
                  POLARITY=True,
                  LINEARIZE=True,
                  PRINT_VAL=True,
                  THR_ONLY=False,
                  params_fbk=[0,0],
                  params_thr=[0,0],
                  THR_e=1000,
                  FBK_V=0.7,
                  OSR=0,
                  DAC_VB=0,
                  service=0):
    HG_mVKe=0.0345
    LG_mVKe=0.0205

    if LOW_GAIN:
        THR_FBK_V=(THR_e/1000.)*LG_mVKe
    else:
        THR_FBK_V=(THR_e/1000.)*HG_mVKe

    if LINEARIZE:
        params_fbk=mat.linearize_DAC(DAC=DAC_VB[1], OSR=OSR, STEPS=32, service=service)
        params_thr=mat.linearize_DAC(DAC=DAC_VB[5], OSR=OSR, STEPS=32, service=service)

    if POLARITY:
        ret_fbk,val_fbk = mat.DAC_lin(DAC=DAC_VB[1], target=FBK_V, params=params_fbk, service=service)
        ret_thr,val_thr = mat.DAC_lin(DAC=DAC_VB[5], target=ret_fbk - THR_FBK_V, params=params_thr, service=service)
    else:
        ret_fbk,val_fbk = mat.DAC_lin(DAC=DAC_VB[1], target=FBK_V, params=params_fbk, service=service)
        ret_thr,val_thr = mat.DAC_lin(DAC=DAC_VB[5], target=ret_fbk + THR_FBK_V, params=params_thr, service=service)
    if PRINT_VAL:
        print('THRESHOLD_TARGET: %.1fe- (%.2fmV)\t'%(THR_e,THR_FBK_V*1000))
        print('THRESHOLD_MEASURED: %.1fmV\tFBK %d\tTHR %d'%((ret_fbk-ret_thr)*1000, val_fbk, val_thr) )

    return (params_fbk,params_thr,val_thr)
