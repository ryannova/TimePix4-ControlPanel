import tkinter as tk
from tkinter import BooleanVar, ttk
from tkinter.constants import DISABLED

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np
import random
from numpy.__config__ import show

root = tk.Tk()
root.geometry("1280x720")

root.title("TimePix Control Panel")

#-------------MENU BAR---------------------#
menubar = tk.Menu(root, background='white', foreground='black', activebackground='lightblue', activeforeground='black')

#Creating File tab in menubar
file = tk.Menu(menubar, tearoff=False)
file.add_command(label="Load Picture...")  
file.add_command(label="Save Picture...") 
#file.add_separator()  
file.add_command(label="Exit", command=root.quit)  
menubar.add_cascade(label="File", menu=file)

#Creating Options tab in menubar
options = tk.Menu(menubar, tearoff=False)

saveFrameRange = tk.BooleanVar()
saveFrameRange.set(True)
loadFrameRange = tk.BooleanVar()
loadFrameRange.set(True)
instantRangeUpdate = tk.BooleanVar()
instantRangeUpdate.set(True)
ignoreMaskedPixel = tk.BooleanVar()
ignoreMaskedPixel.set(False)
asynchronusUpdate = tk.BooleanVar()
asynchronusUpdate.set(False)

options.add_checkbutton(label="Save Frame Range", onvalue=1, offvalue=0, variable=saveFrameRange)
options.add_checkbutton(label="Load Frame Range", onvalue=1, offvalue=0, variable=loadFrameRange)#, command=darkMode)
options.add_checkbutton(label="Instant Range Update", onvalue=1, offvalue=0, variable=instantRangeUpdate)
options.add_separator()
options.add_checkbutton(label="Ignore Masked Pixel", onvalue=1, offvalue=0, variable=ignoreMaskedPixel)
options.add_separator()
options.add_checkbutton(label="Asynchronous Update", onvalue=1, offvalue=0, variable=asynchronusUpdate)
options.add_cascade(label="Max Auto Updates")
options.add_separator()
options.add_command(label="Preferences...")
menubar.add_cascade(label="Options", menu=options)

#Creating View tab in menubar
view = tk.Menu(menubar, tearoff=False)
mirrorImage = tk.BooleanVar()
mirrorImage.set(False)
ensureAspectRatio = tk.BooleanVar()
ensureAspectRatio.set(False)
interpolateImage = tk.BooleanVar()
interpolateImage.set(False)
showGrid = tk.BooleanVar()
showGrid.set(False)
showChipPositions = tk.BooleanVar()
showChipPositions.set(False)

view.add_checkbutton(label="Mirror Image", onvalue=1, offvalue=0, variable=mirrorImage)
view.add_cascade(label="RotateImage")
view.add_separator()
view.add_cascade(label="Set Size")
view.add_checkbutton(label="Ensure Aspect Ratio", onvalue=1, offvalue=0, variable=ensureAspectRatio)
view.add_checkbutton(label="Interpolate Image", onvalue=1, offvalue=0, variable=interpolateImage)
view.add_checkbutton(label="Show Grid", onvalue=1, offvalue=0, variable=showGrid)
view.add_checkbutton(label="Show Chip Position", onvalue=1, offvalue=0, variable=showChipPositions, state=DISABLED)

menubar.add_cascade(label="View", menu=view)

#Creating Service Frames tab in menubar
serviceFrames = tk.Menu(menubar, tearoff=False)

maskBits = tk.BooleanVar()
maskBits.set(False)
testBits = tk.BooleanVar()
testBits.set(False)
THLAdj = tk.BooleanVar()
THLAdj.set(False)
THHAdj = tk.BooleanVar()
mode = tk.BooleanVar()
mode.set(False)
gainMode = tk.BooleanVar()
gainMode.set(False)

serviceFrames.add_checkbutton(label="Mask Bits", onvalue=1, offvalue=0, variable=maskBits)
serviceFrames.add_checkbutton(label="Test Bits", onvalue=1, offvalue=0, variable=testBits)
serviceFrames.add_checkbutton(label="THL Adj.", onvalue=1, offvalue=0, variable=THLAdj)
serviceFrames.add_checkbutton(label="THH Adj.", onvalue=1, offvalue=0, variable=THHAdj)
serviceFrames.add_checkbutton(label="Mode", onvalue=1, offvalue=0, variable=mode, state=DISABLED)
serviceFrames.add_checkbutton(label="Gain Mode", onvalue=1, offvalue=0, variable=gainMode, state=DISABLED)

menubar.add_cascade(label="Service Frames", menu=serviceFrames)








#-------------APPLICATION-----------------------#

graphFrame = root#tk.Frame(root, height=1000, width=600)

fig = Figure(figsize=(5, 4), dpi=100)
t = np.zeros(256*256)
for i in range(256):
    t[random.randint(0,256*256)] = random.randint(0,256)
t.resize(256,256)
sp = fig.add_subplot(111).imshow(t)
fig.colorbar(sp)

canvas = FigureCanvasTkAgg(fig, master=graphFrame)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, graphFrame)
toolbar.update()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


button = tk.Button(master=graphFrame, text="Quit", command=_quit)
button.pack(side=tk.BOTTOM)

#graphFrame.grid()

root.config(menu=menubar)

root.mainloop()