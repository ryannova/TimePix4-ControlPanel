import sys
from PyQt5.QtGui import QDropEvent
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QLine, Qt
from PyQt5.QtWidgets import *
import time

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
        imv = pg.ImageView()
        data = np.random.normal(size=256*256)
        data.resize(256,256)
        imv.setImage(data)
        imv.ui.histogram.hide()
        imv.ui.roiBtn.hide()
        imv.ui.menuBtn.hide()
        layout.addWidget(imv)

        #Creating Toolbar on Right
        toolbar = QWidget()
        toolbar.setFixedWidth(350)#265)
        toolbarLayout = QVBoxLayout()

        frameToolLayout = QHBoxLayout()
        frameToolLayout.addWidget(QLabel("Frame"))
        frameToolLayout.addWidget(QSpinBox())
        frameToolLayout.addWidget(QPushButton("Update"))
        frameToolLayout.addWidget(QPushButton("<"))
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
        toolbar.setLayout(toolbarLayout)
        
        layout.addWidget(toolbar)
        window.setLayout(layout)

        self.setCentralWidget(window)

        self._createActions()
        self._createMenuBar()

    start_time = time.time()
    
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

