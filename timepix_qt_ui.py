from logging import error
import sys
from PyQt5.QtGui import QDropEvent
from PyQt5.QtCore import QThread, pyqtSignal
from numpy.core import overrides
from numpy.core.fromnumeric import size
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QLine, Qt
from PyQt5.QtWidgets import *
import time
import socket
import queue

import tp4

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class TP4ImageViewControl(QWidget):
    set_img = pyqtSignal(int)
    histogram_img = pyqtSignal(int)

    def __init__(self, autoLevel=True):
        super(TP4ImageViewControl, self).__init__()
        self.setFixedWidth(350)
        toolbarLayout = QVBoxLayout()

        
        frameToolLayout = QHBoxLayout()
        frameToolLayout.addWidget(QLabel("Frame"))
        self.frameCounterTool = QSpinBox()
        self.frameCounterTool.valueChanged.connect(self.setImgFrame)
        frameToolLayout.addWidget(self.frameCounterTool)

        self.updateFrame = QPushButton("Update")
        self.updateFrame.setCheckable(True)
        self.updateFrame.setChecked(True)
        self.updateFrame.pressed.connect(self.imageUpdateChange)
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
        self.updateAutoLevel(True)
        self.autoLevel.stateChanged.connect(self.updateAutoLevel)
        graphControlLayout.addWidget(self.autoLevel, 0, 0)
        graphControlLayout.addWidget(QComboBox(), 0, 1)
        graphControlLayout.addWidget(QCheckBox("Count Rate"), 1, 0)
        graphControlLayout.addWidget(QLabel("Time:"), 1, 1)
        self.histogram = QCheckBox("Histogram: ")
        self.histogram.stateChanged.connect(self.histogram_img)
        graphControlLayout.addWidget(self.histogram, 2, 0)
        graphControlLayout.addWidget(QPushButton("Auto refine"), 2, 1)
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
        toolbarLayout.addWidget(QTextEdit())
        
        graphSettingsLayout = QGridLayout()
        graphSettingsLayout.addWidget(QLabel("Color map:"), 0, 0)
        graphSettingsLayout.addWidget(QComboBox(), 0, 1)
        graphSettingsLayout.addWidget(QLabel("Filter chain:"), 1, 0)
        graphSettingsLayout.addWidget(QComboBox(), 1, 1)
        toolbarLayout.addLayout(graphSettingsLayout)
        
        toolbarLayout.addWidget(QCheckBox("Auto Update Preview"))
        self.setLayout(toolbarLayout)

    def imageUpdateChange(self):
        if not self.updateFrame.isChecked():
            self.histogram.setChecked(False)

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

    def updateAutoLevel(self, autoLevel):
        self.minLevel.setDisabled(autoLevel)
        self.minLevelSlider.setDisabled(autoLevel)
        self.minLevelLock.setDisabled(autoLevel)
        self.maxLevel.setDisabled(autoLevel)
        self.maxLevelSlider.setDisabled(autoLevel)
        self.maxLevelLock.setDisabled(autoLevel)

class TimePixImageFetcher(QThread):
    imageUpdated = pyqtSignal(np.ndarray)

    def __init__(self, imgViewer : pg.ImageView, host="127.0.0.1", port=2686, fps=60):
        super().__init__()
        self.imgViewer = imgViewer

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.img = np.zeros(512*512)
        self.sock.bind((host, port))

        self.counter = 0
        self.integrate_mode = 0
        self.fps = fps
    
    def run(self):
        while True:
            packet = self.sock.recvfrom(tp4.PACKET_SIZE)

            for i in range(tp4.HEADER_SIZE,len(packet[0])):
                self.img[(self.counter*128*128) + i - tp4.HEADER_SIZE] += packet[0][i]
            self.counter += 1

            if self.counter >= 16:
                img = np.reshape(self.img, (512,512))
                self.imageUpdated.emit(img)
                if not self.integrate_mode:
                    self.img = np.zeros(512*512)
                self.counter = 0
                time.sleep(1/self.fps)

class TimepixControl(QMainWindow):
    """Main Window"""
    def __init__(self, buffer_size=1000, parent=None):
        """Initializer"""
        super().__init__(parent)
        self.setWindowTitle("Timepix Control")
        self.resize(1200,800)
        self.img_buffer = np.zeros((buffer_size, 512, 512))
        self.img_buffer_size = buffer_size
        self.img_buffer_ptr = 0
        self.buffer_filled = False

        #Create Centeral Widgets with underlying Layout
        window = QWidget()
        layout = QHBoxLayout()

        #Create Image Viewer on Left
        self.imgViewer = pg.ImageView()
        #self.imgViewer.ui.histogram.hide()
        self.imgViewer.ui.roiBtn.hide()
        self.imgViewer.ui.menuBtn.hide()
        layout.addWidget(self.imgViewer)

        self.tp4_image_fetcher = TimePixImageFetcher(self.imgViewer)
        self.tp4_image_fetcher.imageUpdated.connect(self.updateImageViewer)
        self.tp4_image_fetcher.start()

        self.imgViewerControl = TP4ImageViewControl()
        self.imgViewerControl.updateLevelRange(-10,254+10)
        self.imgViewerControl.frameCounterTool.setMaximum(buffer_size)
        self.imgViewerControl.set_img.connect(self.setImageFromBuffer)
        self.imgViewerControl.histogram_img.connect(self.setHistogramImage)
        layout.addWidget(self.imgViewerControl)
        window.setLayout(layout)

        self.setCentralWidget(window)

        self._createActions()
        self._createMenuBar()

    start_time = time.time()

    def setImageFromBuffer(self, index):
        if self.buffer_filled:
            self.imgViewer.setImage(self.img_buffer[(index + self.img_buffer_ptr) % self.img_buffer_size], autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())
        else:
            self.imgViewer.setImage(self.img_buffer[index], autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())

        self.imgViewerControl.updateLevelRange(int(self.imgViewer._imageLevels[0][0])-10, int(self.imgViewer._imageLevels[0][1])+10)
        
        if self.imgViewerControl.autoLevel.isChecked():
            self.imgViewerControl.minLevel.setText(str(int(self.imgViewer.levelMin)))
            self.imgViewerControl.maxLevel.setText(str(int(self.imgViewer.levelMax)))
            
    
    def setHistogramImage(self, state):
        if self.imgViewerControl.updateFrame.isChecked() or not state:
            return
        self.imgViewer.setImage(np.sum(self.img_buffer, axis=0), autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())

        self.imgViewerControl.updateLevelRange(int(self.imgViewer._imageLevels[0][0])-10, int(self.imgViewer._imageLevels[0][1])+10)

        if self.imgViewerControl.autoLevel.isChecked():
            self.imgViewerControl.minLevel.setText(str(int(self.imgViewer.levelMin)))
            self.imgViewerControl.maxLevel.setText(str(int(self.imgViewer.levelMax)))

    def updateImageViewer(self, img):
        if not self.imgViewerControl.updateFrame.isChecked():
            return
        self.img_buffer[self.img_buffer_ptr % self.img_buffer_size] = img
        self.imgViewer.setImage(img, autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())

        if self.buffer_filled:
            self.imgViewerControl.frameCounterTool.setValue(self.img_buffer_size)
        else:
            self.imgViewerControl.frameCounterTool.setValue(self.img_buffer_ptr)
        self.img_buffer_ptr = (self.img_buffer_ptr + 1) % self.img_buffer_size
        if self.img_buffer_ptr == 0:
            self.buffer_filled = True
        self.imgViewerControl.updateLevelRange(int(self.imgViewer._imageLevels[0][0])-10, int(self.imgViewer._imageLevels[0][1])+10)

        if self.imgViewerControl.autoLevel.isChecked():
            self.imgViewerControl.minLevel.setText(str(int(self.imgViewer.levelMin)))
            self.imgViewerControl.maxLevel.setText(str(int(self.imgViewer.levelMax)))
        else:
            try:
                self.imgViewer.setLevels(float(self.imgViewerControl.minLevel.text()), float(self.imgViewerControl.maxLevel.text()))
            except ValueError:
                print("Value Error")

    def _createActions(self):
        #Actions for the File Menu
        self.loadPicture = QAction("&Load Picture...", self)
        self.savePicture = QAction("&Save Picture...", self)
        self.exit = QAction("&Exit", self)

        #Actions for the Options Menu
        self.saveFrameRange = QAction("&Save Frame Range", self)
        self.saveFrameRange.setCheckable(True)
        self.saveFrameRange.setChecked(True)
        self.loadFrameRange = QAction("&Load Frame Range", self)
        self.loadFrameRange.setCheckable(True)
        self.loadFrameRange.setChecked(True)
        self.instantRangeUpdate = QAction("&Instant Range Update", self)
        self.instantRangeUpdate.setCheckable(True)
        self.instantRangeUpdate.setChecked(True)
        self.ignoreMaskedPixel = QAction("&Ignore Masked Pixel", self)
        self.ignoreMaskedPixel.setCheckable(True)
        self.ignoreMaskedPixel.setChecked(False)
        self.asyncUpdate = QAction("&Asynchronous Update", self)
        self.asyncUpdate.setCheckable(True)
        self.asyncUpdate.setChecked(False)
        self.prefernces = QAction("&Preferences...")

        #Actions for View Menu
        self.mirrorImage = QAction("&Mirror Image")
        self.mirrorImage.setCheckable(True)
        self.ensureAspectRatio = QAction("&Ensure Aspect Ratio")
        self.ensureAspectRatio.setCheckable(True)
        self.interpolateImage = QAction("&Interpolate Image")
        self.interpolateImage.setCheckable(True)
        self.showGrid = QAction("&Show Grid")
        self.showGrid.setCheckable(True)
        self.showChipPosition = QAction("&Show Chip Position")
        self.showChipPosition.setCheckable(True)

        #Actions for Service Frame Menu
        self.maskBits = QAction("Mask Bits")
        self.maskBits.setCheckable(True)
        self.testBits = QAction("Test Bits")
        self.testBits.setCheckable(True)
        self.THLAdj = QAction("THL Adj.")
        self.THLAdj.setCheckable(True)
        self.THHAdj = QAction("THH Adj.")
        self.THHAdj.setCheckable(True)
        self.mode = QAction("Mode")
        self.mode.setCheckable(True)
        self.mode.setDisabled(True)
        self.gainMode = QAction("Gain Mode")
        self.gainMode.setCheckable(True)
        self.gainMode.setDisabled(True)


    def _createMenuBar(self):
        menuBar = self.menuBar()
        #Creating File Menu Bar
        fileMenu = menuBar.addMenu("File")
        fileMenu.addAction(self.loadPicture)
        fileMenu.addAction(self.savePicture)
        fileMenu.addAction(self.exit)

        #Creating Options Menu Bar
        optionsMenu = menuBar.addMenu("Options")
        optionsMenu.addAction(self.saveFrameRange)
        optionsMenu.addAction(self.loadFrameRange)
        optionsMenu.addAction(self.instantRangeUpdate)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.ignoreMaskedPixel)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.asyncUpdate)
        maxAutoUpdates = optionsMenu.addMenu("Max Auto Updates")

        
        #Creating View Menu Bar
        viewMenu = menuBar.addMenu("View")
        viewMenu.addAction(self.mirrorImage)
        viewMenu.addMenu("Rotate Image")
        viewMenu.addSeparator()
        viewMenu.addMenu("Set Size")
        viewMenu.addAction(self.ensureAspectRatio)
        viewMenu.addAction(self.interpolateImage)
        viewMenu.addAction(self.showGrid)
        viewMenu.addAction(self.showChipPosition)
        self.showChipPosition.setDisabled(True)
    
        
        #Creating Service Menu Bar
        serviceMenu = menuBar.addMenu("Service Frames")
        serviceMenu.addAction(self.maskBits)
        serviceMenu.addAction(self.testBits)
        serviceMenu.addAction(self.THLAdj)
        serviceMenu.addAction(self.THHAdj)
        serviceMenu.addAction(self.mode)
        serviceMenu.addAction(self.gainMode)

        self.setMenuBar(menuBar)

class TimepixToolbar(QWidget):
    def __init__(self, parent=None):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    timepixControl = TimepixControl()
    timepixControl.show()
    sys.exit(app.exec_())

