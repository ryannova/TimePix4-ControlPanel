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
import time

class SampleApp(tk.Tk):
    start_time = 0
    t = None
    canvas = None
    fig = None
    def __init__(self, *args, **kwargs):
        self.start_time = time.time()
        tk.Tk.__init__(self, *args, **kwargs)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.t = np.zeros(256*256)
        for i in range(256):
            self.t[random.randint(0,256*256)] = random.randint(0,256)
        self.t.resize(256,256)
        sp = self.fig.add_subplot(111).imshow(self.t)
        #self.fig.colorbar(sp)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.update_clock()

    def update_clock(self):
        for i in range(256):
            self.t[random.randint(0,255)][random.randint(0,255)] = random.randint(0,256)
        self.fig.clear()
        sp = self.fig.add_subplot(111).imshow(self.t)
        self.fig.colorbar(sp)

        self.canvas.draw()
        #self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        # call this function again in one second
        self.after(1, self.update_clock)
        print("%s" % (time.time() - self.start_time))
        self.start_time = time.time()

if __name__== "__main__":
    app = SampleApp()
    app.mainloop()