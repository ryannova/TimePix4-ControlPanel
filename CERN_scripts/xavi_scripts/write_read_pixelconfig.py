import grpc
import rpc
import xavi_config as ec
import numpy as np
import matplotlib.pyplot as plt
import conf_timepix4 as conf_tpix4
import matrix as mat
import api as api

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
                                                                    POLARITY=True,
                                                                    ENABLE_STATUS_PROC=False,
                                                                    BYPASS_DAC_SETTING=True,
                                                                    ENABLE_DLL_COLS=True,
                                                                    ENABLE_TOA=False,
                                                                    ENABLE_TDC=False,
                                                                    service=tpx4Service,
                                                                    peripheral=peripheralService,
                                                                    control=controlService)

        NO_OF_PIXELS = 512 * 448
        ARRAY_SIZE_X=448
        ARRAY_SIZE_Y=512

        conf_in=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        conf_out=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        Comp_in_out=np.zeros(shape=(ARRAY_SIZE_X,ARRAY_SIZE_Y), dtype='int')
        readBackConfig=np.zeros(shape=(ARRAY_SIZE_X*ARRAY_SIZE_Y), dtype='int')

        pixelConfig = np.zeros(shape=(2,224,16,32), dtype=np.uint8)
        pixelSPConfig = np.zeros(shape=(2,224,16), dtype=np.uint32)
        for X in range(0,ARRAY_SIZE_X,1):
            for Y in range(0,ARRAY_SIZE_Y,1):
                addr=mat.addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
                pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]=np.random.randint(0, 255)
                conf_in[X][Y]=pixelConfig[addr[0]][addr[1]][addr[2]][addr[3]]

        tpx4Service.ConfigPixels(rpc.Tpx4PixelConfig(idx = 0, config=pixelConfig.tobytes()))

        print('sent')

        readBackConfig = np.frombuffer(tpx4Service.ConfigGetPixels(rpc.ChipIndex(idx = 0)).config, dtype=np.uint8)
        rr= np.reshape(readBackConfig, (2,224,16,32))
        print('received')
        # readBackConfig = np.frombuffer(tpx4Service.ConfigGetPixels(rpc.ChipIndex(idx = 0)).config, dtype=np.uint8)
        # rr= np.reshape(readBackConfig, (2,224,16,32))
        # print('received2')

        # print(readBackConfig.shape)
        # print(readBackConfig[0]," ",readBackConfig[NO_OF_PIXELS-1])

        for X in range(0,ARRAY_SIZE_X,1):
            for Y in range(0,ARRAY_SIZE_Y,1):
                addr=mat.addr_ColRow_to_EoCSpPix(Col=X, Row=Y)
                conf_out[X][Y]=rr[addr[0]][addr[1]][addr[2]][addr[3]]
                if conf_out[X][Y] != conf_in[X][Y] :
                    print("At (%3d,%3d) written=%02x, readback=%02x" % (X,Y, conf_in[X][Y], conf_out[X][Y]))
                    Comp_in_out[X][Y]=1

        fig, axs = plt.subplots(1, 3,figsize = (16,8))

        axs[0].imshow(np.flip(np.rot90(conf_in),0),vmin=0, vmax=255)
        axs[1].imshow(np.flip(np.rot90(conf_out), 0),vmin=0, vmax=255)
        axs[2].imshow(np.flip(np.rot90(Comp_in_out), 0),vmin=0, vmax=1)
        axs[0].set_title("Written")
        axs[1].set_title("Read-back")
        axs[2].set_title("Outliers")
        axs[0].set_ylabel("Cols")
        axs[0].set_xlabel("Rows")
        axs[1].set_xlabel("Rows")

        plt.show()
