import sys
from PyQt5.QtCore import QThread, pyqtSignal
from pyqtgraph.Qt import QtGui
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import time
import socket

from timepix_utils import *
import tp4


pg.setConfigOption('background', 'w')

class CursorDetails(QLabel):
    textFormat = """[X,Y]:\t\t[{x_val},{y_val}]
Count:\t\t{count}
Min:\t\t{min}
Max:\t\t{max}
Total:\t\t{total}
Mean:\t\t{mean}
Std. dev.:\t{std}\n\n"""
    def __init__(self, x_val=0, y_val=0, count=0, min=0, max=0, total=0, mean=0, std=0):
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

class TP4ImageViewControl(QWidget):
    set_img = pyqtSignal(int)
    histogram_img = pyqtSignal(int)
    update_image = pyqtSignal(np.ndarray)
    update_image_none = pyqtSignal()

    def __init__(self, autoLevel=True):
        super(TP4ImageViewControl, self).__init__()
        self.setFixedWidth(350)
        toolbarLayout = QVBoxLayout()

        frameToolLayout = QHBoxLayout()
        frameToolLayout.addWidget(QLabel("Frame"))
        self.frameCounterTool = QSpinBox()
        self.frameCounterTool.valueChanged.connect(self.setImgFrame)
        frameToolLayout.addWidget(self.frameCounterTool)

        self.updateFrame = QPushButton("Start")
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
        #self.histogram.stateChanged.connect(self.histogram_img)
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
        self.cursorDetails = CursorDetails()
        toolbarLayout.addWidget(self.cursorDetails)
        
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
        self.update_image_none.emit()
    
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



class TimepixImageTabs(QWidget):
    modeChanged = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        imgTabsLayout = QHBoxLayout()
        self.frameButton = QPushButton("Frame")
        self.frameButton.setCheckable(True)
        self.frameButton.pressed.connect(self.framePressed)
        self.frameButton.setChecked(True)
        self.maskButton = QPushButton("Mask")
        self.maskButton.setCheckable(True)
        self.maskButton.pressed.connect(self.maskPressed)
        self.testButton = QPushButton("Test")
        self.testButton.setCheckable(True)
        self.testButton.pressed.connect(self.testPressed)
        self.thlButton = QPushButton("THL")
        self.thlButton.setCheckable(True)
        self.thlButton.pressed.connect(self.thlPressed)
        imgTabsLayout.addWidget(self.frameButton)
        imgTabsLayout.addWidget(self.maskButton)
        imgTabsLayout.addWidget(self.testButton)
        imgTabsLayout.addWidget(self.thlButton)

        self.checkedButton = self.frameButton

        self.setLayout(imgTabsLayout)
    
    def framePressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.frameButton
        self.modeChanged.emit(ImageModes.Imaging)

    def maskPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.maskButton
        self.modeChanged.emit(ImageModes.Mask)

    def testPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.testButton
        self.modeChanged.emit(ImageModes.Test)

    def thlPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.thlButton
        self.modeChanged.emit(ImageModes.THL)
    
class ImageControlModes():
    Point = 1
    Row = 2
    Column = 3
    Area = 4

class TimePixImageControls(QWidget):
    modeChanged = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        imgTabsLayout = QHBoxLayout()
        self.pointButton = QPushButton("Point")
        self.pointButton.setCheckable(True)
        self.pointButton.pressed.connect(self.pointPressed)
        self.pointButton.setChecked(True)
        self.rowButton = QPushButton("Row")
        self.rowButton.setCheckable(True)
        self.rowButton.pressed.connect(self.rowPressed)
        self.columnButton = QPushButton("Column")
        self.columnButton.setCheckable(True)
        self.columnButton.pressed.connect(self.columnPressed)
        self.areaButton = QPushButton("Area")
        self.areaButton.setCheckable(True)
        self.areaButton.pressed.connect(self.areaPressed)
        self.areaRow = QSpinBox()
        self.areaRow.setValue(3)
        self.areaCol = QSpinBox()
        self.areaCol.setValue(3)
        imgTabsLayout.addWidget(self.pointButton)
        imgTabsLayout.addWidget(self.rowButton)
        imgTabsLayout.addWidget(self.columnButton)
        imgTabsLayout.addWidget(self.areaButton)
        imgTabsLayout.addWidget(self.areaRow)
        imgTabsLayout.addWidget(self.areaCol)

        self.checkedButton = self.pointButton

        self.setLayout(imgTabsLayout)
    
    def pointPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.pointButton
        self.modeChanged.emit(ImageControlModes.Point)

    def columnPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.columnButton
        self.modeChanged.emit(ImageControlModes.Column)

    def rowPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.rowButton
        self.modeChanged.emit(ImageControlModes.Row)

    def areaPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.areaButton
        self.modeChanged.emit(ImageControlModes.Area)

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

        self.img_mode = ImageModes.Imaging
        self.test_image = np.zeros((512,512))
        self.mask_image = np.zeros((512,512))
        self.thl_image = np.zeros((512,512))

        #Create Centeral Widgets with underlying Layout
        window = QWidget()
        layout = QHBoxLayout()

        #Create Image Viewer on Left
        imgLayout = QVBoxLayout()

        self.imgControlMode = ImageControlModes.Point
        self.imgControl = TimePixImageControls()
        self.imgControl.modeChanged.connect(self.changeImageControlMode)
        self.imgControl.setVisible(False)
        imgLayout.addWidget(self.imgControl)

        plot = pg.PlotItem()
        plot.setLabel(axis='left', text='Y-axis')
        plot.setLabel(axis='bottom', text='X-axis')

        self.imgViewer = pg.ImageView(view=plot)
        self.imgViewer.setImage(np.zeros((512,512)))
        self.imgViewer.getView().invertY(False)
        self.imgViewer.ui.histogram.hide()
        self.imgViewer.ui.roiBtn.hide()
        self.imgViewer.ui.menuBtn.hide()
        self.imgViewer.scene.sigMouseMoved.connect(self.mouseMoved)
        self.imgViewer.scene.sigMouseClicked.connect(self.mouseClicked)
        imgLayout.addWidget(self.imgViewer)

        self.imgTabs = TimepixImageTabs()
        self.imgTabs.modeChanged.connect(self.changeImageMode)
        imgLayout.addWidget(self.imgTabs)

        layout.addLayout(imgLayout)

        self.tp4_image_fetcher = TimePixImageFetcher(self.imgViewer)
        self.tp4_image_fetcher.imageUpdated.connect(self.add_new_image_viewer)
        self.tp4_image_fetcher.start()

        self.imgViewerControl = TP4ImageViewControl()
        self.imgViewerControl.updateLevelRange(-10,254+10)
        self.imgViewerControl.frameCounterTool.setMaximum(buffer_size)
        self.imgViewerControl.set_img.connect(self.set_image_from_buffer)
        self.imgViewerControl.histogram_img.connect(self.set_histogram_image)
        self.imgViewerControl.update_image.connect(self.update_image_viewer)
        self.imgViewerControl.update_image_none.connect(self.update_image_viewer)
        layout.addWidget(self.imgViewerControl)
        window.setLayout(layout)

        self.setCentralWidget(window)

        self.tp_menu_bar = TimepixMenuBar()
        self.setMenuBar(self.tp_menu_bar)

    def changeImageControlMode(self, mode):
        self.imgControlMode = mode

    def changeImageMode(self, mode):
        if mode == ImageModes.Imaging:
            self.img_mode = mode
            self.imgViewerControl.updateFrame.setChecked(False)
            self.imgViewer.setImage(self.img_buffer[self.imgViewerControl.frameCounterTool.value()])
            self.imgControl.setVisible(False)
        elif mode == ImageModes.Mask:
            self.img_mode = mode
            self.imgViewerControl.updateFrame.setChecked(False)
            self.imgViewer.setImage(self.mask_image, autoLevels=True)
            self.imgControl.setVisible(True)
        elif mode == ImageModes.Test:
            self.img_mode = mode
            self.imgViewerControl.updateFrame.setChecked(False)
            self.imgViewer.setImage(self.test_image, autoLevels=True)
            self.imgControl.setVisible(True)
        elif mode == ImageModes.THL:
            self.img_mode = mode
            self.imgViewerControl.updateFrame.setChecked(False)
            self.imgViewer.setImage(self.thl_image, autoLevels=True)
            self.imgControl.setVisible(True)

    def mouseMoved(self, pos):
        x = int(self.imgViewer.getImageItem().mapFromScene(pos).x())
        y = int(self.imgViewer.getImageItem().mapFromScene(pos).y())
        if x < 0 or y < 0 or x >= len(self.imgViewer.image) or y >= len(self.imgViewer.image[0]):
            return
        count = self.imgViewer.image[x,y]
        self.imgViewerControl.cursorDetails.setCursorHover(x_val=x, y_val=y, count=count)
    
    def mouseClicked(self, event):
        pos = event.scenePos()
        x = int(self.imgViewer.getImageItem().mapFromScene(pos).x())
        y = int(self.imgViewer.getImageItem().mapFromScene(pos).y())
        if x < 0 or y < 0 or x >= len(self.imgViewer.image) or y >= len(self.imgViewer.image[0]):
            return
        
        if self.img_mode == ImageModes.Imaging:
            return

        if self.img_mode == ImageModes.Mask:
            self.editSetImage(self.mask_image, x, y)
        elif self.img_mode == ImageModes.Test:
            self.editSetImage(self.test_image, x, y)
        elif self.img_mode == ImageModes.THL:
            self.editSetImage(self.thl_image, x, y)
    
    def editSetImage(self, image, row, col):
        if self.imgControlMode == ImageControlModes.Point:
            image[row, col] = 1
        elif self.imgControlMode == ImageControlModes.Row:
            image[:, col] = np.ones(512)
        elif self.imgControlMode == ImageControlModes.Column:
            image[row, :] = np.ones(512)
        elif self.imgControlMode == ImageControlModes.Area:
            boxRow = self.imgControl.areaRow.value()
            boxCol = self.imgControl.areaCol.value()
            image[row : row+int(boxRow), col : col+int(boxCol)] = np.ones((boxRow, boxCol))

        self.imgViewer.setImage(image, autoRange=False, autoLevels=True)


    def set_image_from_buffer(self, index):
        if self.buffer_filled:
            img = self.img_buffer[(index + self.img_buffer_ptr) % self.img_buffer_size]
        else:
            img = self.img_buffer[index]
        
        self.update_image_viewer(img)
            
    
    def set_histogram_image(self, state):
        if self.imgViewerControl.updateFrame.isChecked() or not state:
            return
        self.imgViewer.setImage(np.sum(self.img_buffer, axis=0), autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())

        self.imgViewerControl.updateLevelRange(int(self.imgViewer._imageLevels[0][0])-10, int(self.imgViewer._imageLevels[0][1])+10)

        if self.imgViewerControl.autoLevel.isChecked():
            self.imgViewerControl.minLevel.setText(str(int(self.imgViewer.levelMin)))
            self.imgViewerControl.maxLevel.setText(str(int(self.imgViewer.levelMax)))

    def add_new_image_viewer(self, img):
        if not self.imgViewerControl.updateFrame.isChecked():
            return
        self.img_buffer[self.img_buffer_ptr % self.img_buffer_size] = img

        self.update_image_viewer(img)

        if self.buffer_filled:
            self.imgViewerControl.frameCounterTool.setValue(self.img_buffer_size)
        else:
            self.imgViewerControl.frameCounterTool.setValue(self.img_buffer_ptr)
        self.img_buffer_ptr = (self.img_buffer_ptr + 1) % self.img_buffer_size
        if self.img_buffer_ptr == 0:
            self.buffer_filled = True

    def update_image_viewer(self, img : np.ndarray = None):
        #if img is None:
        #    img = self.imgViewer.getImageItem().image
        self.imgViewer.setImage(img, autoRange=False, autoLevels=self.imgViewerControl.autoLevel.isChecked())

        self.imgViewerControl.cursorDetails.setImageStats(np.min(img), 
                                                        np.max(img), 
                                                        np.sum(img), 
                                                        np.mean(img), 
                                                        np.std(img), 
            count=img[self.imgViewerControl.cursorDetails.x_val, self.imgViewerControl.cursorDetails.y_val])
        
        self.imgViewerControl.updateLevelRange(int(self.imgViewer._imageLevels[0][0])-10, int(self.imgViewer._imageLevels[0][1])+10)

        if self.imgViewerControl.autoLevel.isChecked():
            self.imgViewerControl.minLevel.setText(str(int(self.imgViewer.levelMin)))
            self.imgViewerControl.maxLevel.setText(str(int(self.imgViewer.levelMax)))
        else:
            try:
                self.imgViewer.setLevels(float(self.imgViewerControl.minLevel.text()), float(self.imgViewerControl.maxLevel.text()))
            except ValueError:
                print("Value Error")



class TimepixMenuBar(QMenuBar):
    def __init__(self):
        super(TimepixMenuBar, self).__init__()
        self.create_actions()
        self.create_menu_bar()
    
    def loadPictureAction(self):
        name = QtGui.QFileDialog.getOpenFileName(self, 'Load File')
        print("Loading ", name)
        
    def savePictureAction(self):
        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        print("Saving ", name)
    
    def create_actions(self):
        #Actions for the File Menu
        self.loadPicture = QAction("&Load Picture...", self)
        self.loadPicture.triggered.connect(self.loadPictureAction)
        self.savePicture = QAction("&Save Picture...", self)
        self.savePicture.triggered.connect(self.savePictureAction)
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

    
    def create_menu_bar(self):
        #Creating File Menu Bar
        fileMenu = self.addMenu("File")
        fileMenu.addAction(self.loadPicture)
        fileMenu.addAction(self.savePicture)
        fileMenu.addAction(self.exit)

        #Creating Options Menu Bar
        optionsMenu = self.addMenu("Options")
        optionsMenu.addAction(self.saveFrameRange)
        optionsMenu.addAction(self.loadFrameRange)
        optionsMenu.addAction(self.instantRangeUpdate)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.ignoreMaskedPixel)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.asyncUpdate)
        maxAutoUpdates = optionsMenu.addMenu("Max Auto Updates")

        
        #Creating View Menu Bar
        viewMenu = self.addMenu("View")
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
        serviceMenu = self.addMenu("Service Frames")
        serviceMenu.addAction(self.maskBits)
        serviceMenu.addAction(self.testBits)
        serviceMenu.addAction(self.THLAdj)
        serviceMenu.addAction(self.THHAdj)
        serviceMenu.addAction(self.mode)
        serviceMenu.addAction(self.gainMode)

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    timepixControl = TimepixControl()
    timepixControl.show()
    sys.exit(app.exec_())

