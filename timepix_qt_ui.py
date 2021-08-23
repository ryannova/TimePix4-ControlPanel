import sys
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import time

class TimepixControl(QMainWindow):
    """Main Window"""
    def __init__(self, parent=None):
        """Initializer"""
        super().__init__(parent)
        self.setWindowTitle("Timepix Control")
        self.resize(1000,800)

        #Create Centeral Widgets with underlying Layout
        window = QWidget()
        layout = QHBoxLayout()

        #Create Image Viewer on Left
        imv = pg.ImageView()
        data = np.random.normal(size=256*256)
        data.resize(256,256)
        imv.setImage(data)
        layout.addWidget(imv)

        #Creating Toolbar on Right
        toolbar = QWidget()
        toolbar.setFixedWidth(265)
        toobarLayout = QVBoxLayout()
        toobarLayout.addWidget(QLabel("Frame"))
        toobarLayout.addWidget(QLabel("Min Level"))
        toobarLayout.addWidget(QCheckBox("Lock"))
        toobarLayout.addWidget(QLabel("Max Level"))
        toobarLayout.addWidget(QCheckBox("Lock"))
        toobarLayout.addWidget(QCheckBox("Auto Range"))
        toobarLayout.addWidget(QCheckBox("Count Rate"))
        toobarLayout.addWidget(QCheckBox("Histogram"))
        toobarLayout.addWidget(QLabel("(Value Graph)"))
        toobarLayout.addWidget(QLabel("(Pixel Values)"))
        toobarLayout.addWidget(QLabel("Color map:"))
        toobarLayout.addWidget(QComboBox())
        toobarLayout.addWidget(QLabel("Filter chain:"))
        toobarLayout.addWidget(QComboBox())
        toobarLayout.addWidget(QCheckBox("Auto Update Preview"))
        toolbar.setLayout(toobarLayout)
        
        layout.addWidget(toolbar)
        window.setLayout(layout)

        self.setCentralWidget(window)

        #self.resize(400, 200)
        #label = QLabel("Hello World")
        #label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        #self.setCentralWidget(label)


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
        self.gainMode = QAction("Gain Mode")
        self.gainMode.setCheckable(True)


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    timepixControl = TimepixControl()
    timepixControl.show()
    sys.exit(app.exec_())

