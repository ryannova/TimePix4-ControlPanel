from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import numpy as np
import pyqtgraph as pg
import time
import socket

from timepix_utils import *


# Fetches the images from the network
class TimePixImageFetcher(QThread):
    imageUpdated = pyqtSignal(np.ndarray)

    def __init__(self, imgViewer : pg.ImageView, host="127.0.0.1", port=2686, fps=60):
        super().__init__()
        self.imgViewer = imgViewer

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.img = np.zeros(446*512)
        self.sock.bind((host, port))

        self.counter = 0
        self.integrate_mode = 0
        self.fps = fps
    
    def run(self):
        while True:
            packet = self.sock.recvfrom(PACKET_SIZE)

            for i in range(HEADER_SIZE,len(packet[0])):
                if (self.counter*128*128) + i - HEADER_SIZE >= len(self.img):
                    break
                self.img[(self.counter*128*128) + i - HEADER_SIZE] += packet[0][i]
            self.counter += 1

            if self.counter >= 16:
                img = np.reshape(self.img, (446,512))
                self.imageUpdated.emit(img)
                if not self.integrate_mode:
                    self.img = np.zeros(446*512)
                self.counter = 0
                time.sleep(1/self.fps)

# CursorDetails mangaes the values of the cursor over the a specific images displayed.
# Inherits QLabel and displays stat information regarding the image and pixel image the 
# Cursor is hovering over.
class CursorDetails(QLabel):
    textFormat = """[X,Y]:\t\t[{x_val},{y_val}]
Matrix:\t\t({matrixInfo})
(TOP,EOC,SPGroup,SPixel,Pixel)
Count:\t\t{count}
Min:\t\t{min}
Max:\t\t{max}
Total:\t\t{total}
Mean:\t\t{mean}
Std. dev.:\t{std}\n\n"""
    def __init__(self, x_val : int = 0, y_val=0, count=0, min=0, max=0, total=0, mean=0, std=0):
        super(QLabel, self).__init__()
        self.x_val = x_val
        self.y_val = y_val
        self.count = count
        self.min = min
        self.max = max
        self.total = total
        self.mean = mean
        self.std = std
        self.updateText()
        
    def updateText(self):
        self.setText(self.textFormat.format(x_val=self.x_val, 
                                            y_val=self.y_val,
                                            matrixInfo=image_to_matrix_coordinates(self.x_val, self.y_val),
                                            count=self.count, 
                                            min=self.min, 
                                            max=self.max, 
                                            total=self.total, 
                                            mean=self.mean, 
                                            std=self.std))

    def setCursorHover(self, x_val, y_val, count):
        self.x_val = x_val
        self.y_val = y_val
        self.count = count
        self.updateText()

    def setImageStats(self, min, max, total, mean, std, count=None):
        self.min = min
        self.max = max
        self.total = total
        self.mean = mean
        self.std = std
        if count != None:
            self.count = count
        self.updateText()

class ImageViewConfig():
    def __init__(self, frameNumber : int = 0, minLevel : int = 0, maxLevel : int = 0, 
    autoRange : bool = True, countRate : bool = False, histogram : bool = False, 
    colormap : str = "gray", colormapSource : str = "matplotlib", filterChain : str = "none") -> None:

        self.frameNumber : int = frameNumber
        self.minLevel : int = minLevel
        self.maxLevel : int = maxLevel
        self.autoRange : bool = autoRange
        self.countRate : bool = countRate
        self.histogram : bool = histogram
        self.colormap : str = colormap
        self.colormapSource : str = colormapSource
        self.filterChain :str = filterChain

class TimepixImageControl(QWidget):
    set_img = pyqtSignal(int)
    histogram_img = pyqtSignal(int)
    update_image = pyqtSignal(np.ndarray)
    update_image_config = pyqtSignal()
    update_image_viewer = pyqtSignal(ImageViewConfig)

    color_maps = ["Gray", "Jet", "Hot", "Cool"]
    auto_range_modes = ["Min - Max", "0.01 - 0.99 fractile", "0.05 - 0.95 fractile"]

    def __init__(self, autoLevel=True):
        super(TimepixImageControl, self).__init__()
        self.setFixedWidth(350)

        self.imgViewConfig = ImageViewConfig()

        toolbarLayout = QVBoxLayout()

        frameToolLayout = QHBoxLayout()
        frameToolLayout.addWidget(QLabel("Frame"))
        self.frameCounterTool = QSpinBox()
        self.frameCounterTool.valueChanged.connect(self.setImgFrame)
        frameToolLayout.addWidget(self.frameCounterTool)

        self.updateFrame = QPushButton("Start")
        self.updateFrame.setCheckable(True)
        self.updateFrame.setChecked(True)
        frameToolLayout.addWidget(self.updateFrame)

        self.frameDecrement = QPushButton("<")
        self.frameDecrement.setFixedWidth(30)
        self.frameDecrement.pressed.connect(self.decrementFrame)
        self.frameIncrement = QPushButton(">")
        self.frameIncrement.setFixedWidth(30)
        self.frameIncrement.pressed.connect(self.incrementFrame)
        frameToolLayout.addWidget(self.frameDecrement)
        frameToolLayout.addWidget(self.frameIncrement)
        toolbarLayout.addLayout(frameToolLayout)
        
        toolbarLayout.addWidget(QHLine())
        
        minLevelLayout = QGridLayout()
        minLevelLayout.addWidget(QLabel("Min Level:"), 0, 0)
        self.minLevelLock = QCheckBox("Lock")
        self.minLevelLock.stateChanged.connect(self.minLockStateChanged)
        minLevelLayout.addWidget(self.minLevelLock, 1, 0)
        self.minLevel = QLineEdit()
        self.minLevel.setFixedHeight(28)
        self.minLevel.textChanged.connect(self.updateMinSlider)
        minLevelLayout.addWidget(self.minLevel, 0, 1)
        self.minLevelSlider = QSlider(Qt.Horizontal)
        self.minLevelSlider.sliderMoved.connect(self.updateMinText)
        minLevelLayout.addWidget(self.minLevelSlider, 1, 1)
        minLevelLayout.addWidget(QPushButton("Under\n Warning"), 0, 2)
        toolbarLayout.addLayout(minLevelLayout)

        toolbarLayout.addWidget(QHLine())

        maxLevelLayout = QGridLayout()
        maxLevelLayout.addWidget(QLabel("Max Level:"), 0, 0)
        self.maxLevelLock = QCheckBox("Lock")
        self.maxLevelLock.stateChanged.connect(self.maxLockStateChanged)
        maxLevelLayout.addWidget(self.maxLevelLock, 1, 0)
        self.maxLevel = QLineEdit()
        self.maxLevel.setFixedHeight(28)
        self.maxLevel.textChanged.connect(self.updateMaxSlider)
        maxLevelLayout.addWidget(self.maxLevel, 0, 1)
        self.maxLevelSlider = QSlider(Qt.Horizontal)
        self.maxLevelSlider.sliderMoved.connect(self.updateMaxText)
        maxLevelLayout.addWidget(self.maxLevelSlider, 1, 1)
        maxLevelLayout.addWidget(QPushButton("Over\n Warning"), 0, 2)
        toolbarLayout.addLayout(maxLevelLayout)

        toolbarLayout.addWidget(QHLine())

        graphControlLayout = QGridLayout()
        self.autoLevel = QCheckBox("Auto Range:")
        self.autoLevel.setChecked(autoLevel)
        self.autoLevelStateChanged(True)
        self.autoLevel.stateChanged.connect(self.autoLevelStateChanged)
        graphControlLayout.addWidget(self.autoLevel, 0, 0)
        self.autoRangeMode = QComboBox()
        for a in self.auto_range_modes:
            self.autoRangeMode.addItem(a)
        graphControlLayout.addWidget(self.autoRangeMode, 0, 1)
        graphControlLayout.addWidget(QCheckBox("Count Rate"), 1, 0)
        graphControlLayout.addWidget(QLabel("Time:"), 1, 1)
        self.histogram = QCheckBox("Histogram: ")
        #self.histogram.stateChanged.connect(self.histogram_img)
        graphControlLayout.addWidget(self.histogram, 2, 0)
        self.autoRefine = QPushButton("Auto refine")
        graphControlLayout.addWidget(self.autoRefine, 2, 1)
        toolbarLayout.addLayout(graphControlLayout)

        toolbarLayout.addWidget(QHLine())
        
        graphButtonLayout = QHBoxLayout()
        graphButtonLayout.addWidget(QPushButton("<-"))
        graphButtonLayout.addWidget(QPushButton("->"))
        graphButtonLayout.addWidget(QPushButton("^"))
        graphButtonLayout.addWidget(QPushButton("V"))
        graphButtonLayout.addWidget(QPushButton("+<->"))
        graphButtonLayout.addWidget(QPushButton("-<->"))
        graphButtonLayout.addWidget(QPushButton("+^"))
        graphButtonLayout.addWidget(QPushButton("-^"))
        toolbarLayout.addLayout(graphButtonLayout)

        toolbarLayout.addWidget(QTextEdit())
        self.cursorDetails = CursorDetails()
        toolbarLayout.addWidget(self.cursorDetails)
        
        graphSettingsLayout = QGridLayout()
        graphSettingsLayout.addWidget(QLabel("Color map:"), 0, 0)
        self.colormap = QComboBox()
        for c in self.color_maps:
            self.colormap.addItem(c)
        self.colormap.currentTextChanged.connect(self.onColorMapChanged)
        graphSettingsLayout.addWidget(self.colormap, 0, 1)
        graphSettingsLayout.addWidget(QLabel("Filter chain:"), 1, 0)
        self.filterChain = QComboBox()
        self.filterChain.addItem("None")
        graphSettingsLayout.addWidget(self.filterChain, 1, 1)
        toolbarLayout.addLayout(graphSettingsLayout)
        
        self.autoUpdatePreview = QCheckBox("Auto Update Preview")
        self.autoUpdatePreview.setChecked(True)
        toolbarLayout.addWidget(self.autoUpdatePreview)
        self.setLayout(toolbarLayout)

    def incrementFrame(self):
        if self.updateFrame.isChecked():
            return
        self.frameCounterTool.setValue(self.frameCounterTool.value()+1)
        self.set_img.emit(self.frameCounterTool.value())

    def decrementFrame(self):
        if self.updateFrame.isChecked():
            return
        self.frameCounterTool.setValue(self.frameCounterTool.value()-1)
        self.set_img.emit(self.frameCounterTool.value())

    def setImgFrame(self, index):
        if self.updateFrame.isChecked():
            return
        self.set_img.emit(index)
    
    def updateLevelRange(self, minLevel, maxLevel):
        self.minLevelSlider.setMinimum(minLevel)
        self.minLevelSlider.setMaximum(maxLevel)
        self.maxLevelSlider.setMinimum(minLevel)
        self.maxLevelSlider.setMaximum(maxLevel)
        self.update_image_config.emit()
    
    def updateMinText(self):
        self.minLevel.setText(str(self.minLevelSlider.value()))

    def updateMinSlider(self):
        try:
            self.minLevelSlider.setValue(int(float(self.minLevel.text())))
        except ValueError:
            print("Value Error Min Level")

    def updateMaxText(self):
        self.maxLevel.setText(str(self.maxLevelSlider.value()))

    def updateMaxSlider(self):
        try:
            self.maxLevelSlider.setValue(int(float(self.maxLevel.text())))
        except ValueError:
            print("Value Error Min Level")

    def autoLevelStateChanged(self, state):
        self.minLevelLock.setDisabled(state)
        self.minLevelLock.setChecked(state)
        self.minLockStateChanged(state)
        
        self.maxLevelLock.setDisabled(state)
        self.maxLevelLock.setChecked(state)
        self.maxLockStateChanged(state)
        self.update_image_config.emit()

    def minLockStateChanged(self, state):
        self.minLevel.setDisabled(state)
        self.minLevelSlider.setDisabled(state)

    def maxLockStateChanged(self, state):
        self.maxLevel.setDisabled(state)
        self.maxLevelSlider.setDisabled(state)


    def onColorMapChanged(self, value):
        self.imgViewConfig.colormap = value
        self.update_image_viewer.emit(self.imgViewConfig)

class TimepixImageView(pg.ImageView):
    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, levelMode='mono', *args):
        pg.setConfigOption('background', 'w')
        if view == None:
            view = pg.PlotItem()
            view.setLabel(axis='left', text='Y-axis')
            view.setLabel(axis='bottom', text='X-axis')
        
        super().__init__(parent=parent, name=name, view=view, imageItem=imageItem, levelMode=levelMode, *args)

        self.setImage(np.zeros((446, 512)))
        self.getView().invertY(False)
        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()


def main():
    app = QApplication([])
    window = QWidget()
    layout = QHBoxLayout()
    layout.addWidget(TimepixImageView())
    layout.addWidget(TimepixImageControl())
    window.setLayout(layout)
    window.resize(1200,800)
    window.show()
    app.exec_()
    



if __name__ == "__main__":
    main()