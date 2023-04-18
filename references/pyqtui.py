"""
Display a plot and an image with minimal setup. 

pg.plot() and pg.image() are indended to be used from an interactive prompt
to allow easy data inspection (but note that PySide unfortunately does not
call the Qt event loop while the interactive prompt is running, in this case
it is necessary to call QApplication.exec_() to make the windows appear).
"""

import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import *

#data = np.random.normal(size=1000)
#pg.plot(data, title="Simplest possible plotting example")

app = QApplication([])
window = QWidget()
window.setWindowTitle('PyQt5 App')
window.setGeometry(100, 100, 280, 80)
window.move(60, 15)
helloMsg = QLabel('<h1>Hello World!</h1>', parent=window)
helloMsg.move(60, 15)
window.show()
app.exec_()

#data = np.random.normal(size=(500,500))
#pg.image(data, title="Simplest possible image example")

#if __name__ == '__main__':
    #pg.exec()