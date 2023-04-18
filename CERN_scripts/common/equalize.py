#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm
from matplotlib.ticker import MultipleLocator

def eq_broute_force(fbase, start, to, step):
    scans=[]
    avr=[]
    dacs_range=[]
    RANGE_HIST_MAX=1000
    RANGE_HIST_MIN=-1000
    STEP=50
    for i in range(start,to,step):
        dacs_range.append(i)
    last=dacs_range[len(dacs_range)-1]
    last=len(dacs_range)-1
    print(last, dacs_range)
    fig_s, axs_s = plt.subplots(1, 1, figsize = (8,16))
    for dacc in dacs_range:
        data=np.loadtxt(fbase+"//dac_%d.csv"%dacc)
        num_pixels=len(np.argwhere(data>-10000))
        scans.append(data)

        a=np.average(data[data>-10000])
        std=np.std(data[data>-10000])
        # std_e=std*535/36.1
        avr.append(a)
        print("DAC=%d AVR=%.2f STD=%.2f PIXELS=%d"%(dacc, a, std, num_pixels))
        hist=np.histogram(data, bins=np.arange(RANGE_HIST_MIN,RANGE_HIST_MAX,STEP), density=True)
        axs_s.plot(hist[1][0:int((RANGE_HIST_MAX-RANGE_HIST_MIN)/STEP) - 1], hist[0],'o:', label='%d: [%.2f %.2f]'%(dacc, a, std ))

    target=(avr[14]+avr[17])/2
    # target=-300
    # target=avr[16]
    print ("Target %.2f"%target)
    bestv=np.zeros(scans[0].shape)
    bestcode=np.zeros(scans[0].shape)
    mask=np.zeros(scans[0].shape)
    X,Y=scans[0].shape

    for x in range(X):
        for y in range(Y):
            bestv[x][y]=-10000
            bc=0
            bv=scans[0][x][y]
            for i in range(1,len(dacs_range)):
                # if not scans[i][x][y]:
                # print(i,x,y,bv,bc,abs(bv-target),abs(scans[i][x][y]-target))
                if abs(bv-target)>abs(scans[i][x][y]-target):
                    bc=i
                    bv=scans[i][x][y]
            bestv[x][y]=bv
            bestcode[x][y]=bc

    # for dacc in dacs_range:
    #     print(dacc,scans[dacc][7][252],scans[dacc][7][253],scans[dacc][7][251] )

    np.savetxt(fbase+"//eq_bl.dat",bestv,fmt="%.2f")
    np.savetxt(fbase+"//eq_codes.dat",bestcode,fmt="%d")
    num_pixels=len(np.argwhere(bestv>-10000))
    a=np.average(bestv[bestv>-10000])
    std=np.std(bestv[bestv>-10000])
    hist=np.histogram(bestv, bins=np.arange(RANGE_HIST_MIN,RANGE_HIST_MAX,STEP), density=True)
    axs_s.plot(hist[1][0:int((RANGE_HIST_MAX-RANGE_HIST_MIN)/STEP) - 1], hist[0],'o-r', label='EQ: [%.2f %.2f]'%(a, std ),linewidth=5.0)
    axs_s.legend(loc='upper left') #, bbox_to_anchor=(1.04,1), borderaxespad=0.)
    axs_s.set_xlabel('THR DAC [step]')
    # ax1.set_ylabel('[V]', color='g')
    data=scans[0]
    g0=np.average(data[data>-10000])+ 3.2*np.std(data[data>-10000])
    data=scans[last]
    g1=np.average(data[data>-10000])- 3.2*np.std(data[data>-10000])
    if g1>g0:
        sep= 'SEP:%.2f'%(g1-g0)
    else:
        sep= 'TOO CLOSE SEP:%.2f'%(g1-g0)

    mask = np.where( (bestv>(a-6*std)) & (bestv<(a+6*std)), 0, 1)
    a=np.average(bestv[mask==0])
    std=np.std(bestv[mask==0])
    np.savetxt(fbase+"//eq_mask.dat",mask,fmt="%d")
    # masked=np.argwhere(np.logical_and(mask>0,scans[0]>-10000))
    masked=np.argwhere(mask>0)
    for i in masked:
        tr_s=""
        for tr in range(0,32):
            tr_s+="%3d "%scans[tr][i[0]][i[1]]
        print("[%3d %3d]"%(i[0],i[1]),"%2d"%bestcode[i[0]][i[1]],"%3d"%bestv[i[0]][i[1]],"[",tr_s,"]")

    print("EQUALIZED %s AVR=%.2f STD=%.2f MAX=%d MIN=%d PIXELS=%d MASKED=%d"
          %(sep,a,std,np.max(bestv[mask==0]),np.min(bestv[mask==0]),num_pixels, len(masked)))

    fig, axs = plt.subplots(1, 3, figsize = (15,15))

    bc = axs[0].imshow(np.flip(np.rot90(bestcode),0), origin='lower')
    divider3 = make_axes_locatable(axs[0])
    cax3 = divider3.append_axes("right", size="5%", pad=0.05)
    cbar3 = plt.colorbar(bc, cax=cax3, format="%d")
    axs[0].set_title("daccodes")
    axs[0].set_ylabel("Rows")
    axs[0].set_xlabel("Columns")

    bt = axs[1].imshow(np.flip(np.rot90(bestv),0), origin='lower', vmin=target-5, vmax=target+5)
    divider3 = make_axes_locatable(axs[1])
    cax3 = divider3.append_axes("right", size="5%", pad=0.05)
    cbar3 = plt.colorbar(bt, cax=cax3, format="%d")
    axs[1].set_title("best_thr")
    axs[1].set_ylabel("Rows")
    axs[1].set_xlabel("Columns")

    msk = axs[2].imshow(np.flip(np.rot90(mask),0), origin='lower')
    divider3 = make_axes_locatable(axs[2])
    cax3 = divider3.append_axes("right", size="5%", pad=0.05)
    cbar3 = plt.colorbar(msk, cax=cax3, format="%d")
    axs[2].set_title("masked")
    axs[2].set_ylabel("Rows")
    axs[2].set_xlabel("Columns")

    plt.tight_layout()
    plt.show()

def main():
   # eq_broute_force("/home/timepix4/spidr4/spidr4_python/results/E5_Si/", 0, 32, 1)
   # eq_broute_force("/home/timepix4/spidr4/spidr4_python/results/equalization/", 0, 32, 1)
   eq_broute_force("/home/timepix4/spidr4/spidr4_python/results/W8_Si1/", 0, 32, 1)
if __name__=="__main__":
  main()
