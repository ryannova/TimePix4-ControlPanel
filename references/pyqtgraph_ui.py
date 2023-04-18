from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import time

start_time = time.time()

app = pg.mkQApp("Plotting Example")
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')

win = QtGui.QMainWindow()
win.resize(800,800)
imv = pg.ImageView()
win.setCentralWidget(imv)
win.show()
win.setWindowTitle('pyqtgraph example: ImageView')

def update():
    global imv, start_time
    #dataRed = np.ones((100, 200, 200)) * np.linspace(90, 150, 100)[:, np.newaxis, np.newaxis]
    #dataRed += pg.gaussianFilter(np.random.normal(size=(200, 200)), (5, 5)) * 100
    #dataGrn = np.ones((100, 200, 200)) * np.linspace(90, 180, 100)[:, np.newaxis, np.newaxis]
    #dataGrn += pg.gaussianFilter(np.random.normal(size=(200, 200)), (5, 5)) * 100
    #dataBlu = np.ones((100, 200, 200)) * np.linspace(180, 90, 100)[:, np.newaxis, np.newaxis]
    #dataBlu += pg.gaussianFilter(np.random.normal(size=(200, 200)), (5, 5)) * 100

    #data = np.concatenate(
    #    (dataRed[:, :, :, np.newaxis], dataGrn[:, :, :, np.newaxis], dataBlu[:, :, :, np.newaxis]), axis=3
    #)
    
    data = np.random.normal(size=256*256)
    data.resize(256,256)
    #imv.setImage(data, xvals=np.linspace(1., 3., data.shape[0]))
    imv.setImage(data)

    print("%s" % (time.time() - start_time))
    start_time = time.time()


update()
## Set a custom color map
colors = [
    (0, 0, 0),
    (45, 5, 61),
    (84, 42, 55),
    (150, 87, 60),
    (208, 171, 141),
    (255, 255, 255)
]
cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
imv.setColorMap(cmap)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)


if __name__ == '__main__':
    pg.exec()