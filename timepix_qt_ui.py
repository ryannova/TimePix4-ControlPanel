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

    def __init__(self, autoLevel=True):
        super(TP4ImageViewControl, self).__init__()
        self.setFixedWidth(350)
        toolbarLayout = QVBoxLayout()

        
        frameToolLayout = QHBoxLayout()
        frameToolLayout.addWidget(QLabel("Frame"))
        self.frameCounterTool = QSpinBox()
        frameToolLayout.addWidget(self.frameCounterTool)

        self.updateFrame = QPushButton("Update")
        frameToolLayout.addWidget(self.updateFrame)

        self.frameDecrement = QPushButton("<")
        self.frameDecrement.setFixedWidth(30)
        self.frameIncrement = QPushButton(">")
        self.frameIncrement.setFixedWidth(30)
        #frameToolLayout.addWidget()
        frameToolLayout.addWidget(self.frameDecrement)
        frameToolLayout.addWidget(self.frameIncrement)
        toolbarLayout.addLayout(frameToolLayout)
        
        toolbarLayout.addWidget(QHLine())
        
        minLevelLayout = QGridLayout()
        minLevelLayout.addWidget(QLabel("Min Level:"), 0, 0)
        self.minLevelLock = QCheckBox("Lock")
        minLevelLayout.addWidget(self.minLevelLock, 1, 0)
        self.minLevel = QTextEdit()
        self.minLevel.setFixedHeight(28)
        minLevelLayout.addWidget(self.minLevel, 0, 1)
        self.minLevelSlider = QSlider(Qt.Horizontal)
        minLevelLayout.addWidget(self.minLevelSlider, 1, 1)
        minLevelLayout.addWidget(QPushButton("Under\n Warning"), 0, 2)
        toolbarLayout.addLayout(minLevelLayout)

        toolbarLayout.addWidget(QHLine())

        minLevelLayout = QGridLayout()
        minLevelLayout.addWidget(QLabel("Min Level:"), 0, 0)
        self.maxLevelLock = QCheckBox("Lock")
        minLevelLayout.addWidget(self.maxLevelLock, 1, 0)
        self.maxLevel = QTextEdit()
        self.maxLevel.setFixedHeight(28)
        minLevelLayout.addWidget(self.maxLevel, 0, 1)
        self.maxLevelSlider = QSlider(Qt.Horizontal)
        minLevelLayout.addWidget(self.maxLevelSlider, 1, 1)
        minLevelLayout.addWidget(QPushButton("Over\n Warning"), 0, 2)
        toolbarLayout.addLayout(minLevelLayout)

        toolbarLayout.addWidget(QHLine())

        graphControlLayout = QGridLayout()
        self.autoLevel = QCheckBox("Auto Range:")
        self.autoLevel.setChecked(autoLevel)
        graphControlLayout.addWidget(self.autoLevel, 0, 0)
        graphControlLayout.addWidget(QComboBox(), 0, 1)
        graphControlLayout.addWidget(QCheckBox("Count Rate"), 1, 0)
        graphControlLayout.addWidget(QLabel("Time:"), 1, 1)
        graphControlLayout.addWidget(QCheckBox("Histogram: "), 2, 0)
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
    
    def setLevels(minLevel, maxLevel, levelRange):
        print(minLevel, maxLevel, levelRange)

    def update(self):
        isAutoLevel = self.autoLevel.isChecked()
        self.minLevel.setDisabled(isAutoLevel)
        self.minLevelSlider.setDisabled(isAutoLevel)
        self.minLevelLock.setDisabled(isAutoLevel)
        self.maxLevel.setDisabled(isAutoLevel)
        self.maxLevelSlider.setDisabled(isAutoLevel)
        self.maxLevelLock.setDisabled(isAutoLevel)

    def _create_Widgets():
        pass

    def _create_Layout():
        pass

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
        #self.imgViewer.ui.histogram.hide()
        self.imgViewer.ui.roiBtn.hide()
        self.imgViewer.ui.menuBtn.hide()
        layout.addWidget(self.imgViewer)

        self.tp4_image_fetcher = TimePixImageFetcher(self.imgViewer)
        self.tp4_image_fetcher.imageUpdated.connect(self.updateImageViewer)
        self.tp4_image_fetcher.start()

        self.imgViewerControl = TP4ImageViewControl()
        
        layout.addWidget(self.imgViewerControl)
        window.setLayout(layout)

        self.setCentralWidget(window)

        self._createActions()
        self._createMenuBar()

    start_time = time.time()

    def updateImageViewer(self, img):
        self.imgViewer.setImage(img, autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())

        #self.imgViewerControl.setLevels(self.imgViewer.levelMin, self.imgViewer.levelMax, levelRange=self.imgViewer.quickMinMax(self.imgViewer.imageDisp))

        self.imgViewerControl.update()
        self.imgViewerControl.minLevel.setPlainText(str(self.imgViewer.levelMin))
        self.imgViewerControl.maxLevel.setPlainText(str(self.imgViewer.levelMax))

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

