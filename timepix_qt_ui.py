from logging import error
import sys
from PyQt5.QtGui import QDropEvent
from PyQt5.QtCore import QThread, pyqtSignal
from numpy.core import overrides
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QLine, Qt
from PyQt5.QtWidgets import *
import time
import socket
import queue

import tp4


class TimepixControlToolbar(QWidget):
    frameChanged = pyqtSignal(int) #emits when there is a new frame selected

    def __init__(self):
        super(TimepixControlToolbar, self).__init__()
        self.setFixedWidth(350)
        toolbarLayout = QVBoxLayout()

        
        frameToolLayout = QHBoxLayout()
        frameToolLayout.addWidget(QLabel("Frame"))
        self.frameCounterTool = QSpinBox()
        self.frameCounterTool.valueChanged.connect(self._emit_frameChanged)
        frameToolLayout.addWidget(self.frameCounterTool)

        self.updateFrameButton = QPushButton("Update")
        frameToolLayout.addWidget(self.updateFrameButton)

        self.frameIncrement = QPushButton("<")
        self.frameIncrement = QPushButton(">")
        #frameToolLayout.addWidget()
        frameToolLayout.addWidget(QPushButton(">"))
        toolbarLayout.addLayout(frameToolLayout)
        
        
        minLevelLayout = QGridLayout()
        minLevelLayout.addWidget(QLabel("Min Level:"), 0, 0)
        minLevelLayout.addWidget(QCheckBox("Lock"), 1, 0)
        minLevelLayout.addWidget(QTextEdit(), 0, 1)
        minLevelLayout.addWidget(QSlider(Qt.Horizontal), 1, 1)
        minLevelLayout.addWidget(QPushButton("Under\n Warning"), 0, 2)
        toolbarLayout.addLayout(minLevelLayout)

        minLevelLayout = QGridLayout()
        minLevelLayout.addWidget(QLabel("Min Level:"), 0, 0)
        minLevelLayout.addWidget(QCheckBox("Lock"), 1, 0)
        minLevelLayout.addWidget(QTextEdit(), 0, 1)
        minLevelLayout.addWidget(QSlider(Qt.Horizontal), 1, 1)
        minLevelLayout.addWidget(QPushButton("Over\n Warning"), 0, 2)
        toolbarLayout.addLayout(minLevelLayout)

        graphControlLayout = QGridLayout()
        graphControlLayout.addWidget(QCheckBox("Auto Range:"), 0, 0)
        graphControlLayout.addWidget(QComboBox(), 0, 1)
        graphControlLayout.addWidget(QCheckBox("Count Rate"), 1, 0)
        graphControlLayout.addWidget(QLabel("Time:"), 1, 1)
        graphControlLayout.addWidget(QCheckBox("Histogram: "), 2, 0)
        graphControlLayout.addWidget(QPushButton("Auto refine"), 2, 1)
        toolbarLayout.addLayout(graphControlLayout)
        
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
    
    def _emit_frameChanged(self, newFrame):
        self.frameChanged.emit(newFrame)

    def _create_Widgets():
        pass

    def _create_Layout():
        pass

class TimePixImageFetcher(QThread):
    def __init__(self, imgViewer : pg.ImageView, host="127.0.0.1", port=2686, buffer_size=1000):
        super().__init__()
        self.imgViewer = imgViewer

        self.packet_buffer = queue.Queue(maxsize=buffer_size)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.img = np.array([])


        self.sock.bind((host, port))
        self.counter = 0
    
    def run(self):
        while True:
            print("Gathering Data", self.counter)
            packet = self.sock.recvfrom(tp4.PACKET_SIZE)
            self.counter += 1

            data = np.array([i for i in packet[0]])

            self.img = np.append(self.img, data)
            if self.counter >= 16:
                self.img.resize(512,512)
                self.imgViewer.setImage(self.img)
                self.img = np.array([])
                self.counter = 0
                time.sleep(0.016)
            #data.resize(128,128)
            #self.imgViewer.setImage(data)
            #time.sleep(0.016)

class TimepixControl(QMainWindow):
    """Main Window"""
    def __init__(self, parent=None):
        """Initializer"""
        super().__init__(parent)
        self.setWindowTitle("Timepix Control")
        self.resize(1200,800)

        #Create Centeral Widgets with underlying Layout
        window = QWidget()
        layout = QHBoxLayout()

        #Create Image Viewer on Left
        self.imgViewer = pg.ImageView()
        data = np.random.normal(size=128*128)
        data.resize(128,128)
        self.imgViewer.setImage(data)
        self.imgViewer.ui.histogram.hide()
        self.imgViewer.ui.roiBtn.hide()
        self.imgViewer.ui.menuBtn.hide()
        layout.addWidget(self.imgViewer)

        self.tp4_image_fetcher = TimePixImageFetcher(self.imgViewer)
        self.tp4_image_fetcher.start()


        self.toolbar = TimepixControlToolbar()
        #self.toolbar.printTestSignal.connect(self.printTest)
        
        layout.addWidget(self.toolbar)
        window.setLayout(layout)

        self.setCentralWidget(window)

        self._createActions()
        self._createMenuBar()

    start_time = time.time()
    
    def printTest(self, value):
        print("Value Changed ", value)

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

