####################################################################################
# Main Timepix 4 User Interface. 
# Contains most of the utilities for viewing images and communicating with the chips
####################################################################################
from io import FileIO
import sys
from PyQt5.QtCore import pyqtSignal, QPoint, QRect
from pyqtgraph.Qt import QtGui
from PyQt5.QtGui import QPainter, QBrush, QColor
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import *

from timepix_utils import *
from timepix_image import *
from timepix_edit_image import *
from timepix_IO import timepix_xml

# Changing major configuration in the pyqtgraph library.
pg.setConfigOption("leftButtonPan", False)

# Main Window for Timepix Control GUI. 
# This class calls all other classes for each component of the interface 
# and should be the only class interacting directly with the user. Any user
# interactions with other classes should be passed in through function calls and signals
class TimepixControl(QMainWindow):
    def __init__(self, buffer_size=1000, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timepix Control")
        self.resize(1200,800)
        self.img_buffer = np.zeros((buffer_size, 446, 512))
        self.img_buffer_size = buffer_size
        self.img_buffer_ptr = 0
        self.buffer_filled = False

        self.img_mode = ImageModes.Imaging

        #Create Centeral Widgets with underlying Layout
        window = QWidget()
        layout = QHBoxLayout()

        #Create Image Viewer on Left
        imgLayout = QVBoxLayout()

        self.matrixConfig = TimepixMatrixConfig()
        self.matrixConfig.imageChanged.connect(self.changeImageMode)
        self.matrixConfig.setEditControlsVisible(False)
        self.matrixConfig.setVisible(False)
        imgLayout.addWidget(self.matrixConfig)

        self.imgViewer = TimepixImageView()
        self.imgViewer.scene.sigMouseMoved.connect(self.mouseMoved)
        self.imgViewer.scene.sigMouseClicked.connect(self.mouseClicked)
        imgLayout.addWidget(self.imgViewer)

        layout.addLayout(imgLayout)

        self.tp4_image_fetcher = TimePixImageFetcher(self.imgViewer)
        self.tp4_image_fetcher.imageUpdated.connect(self.add_new_image_viewer)
        self.tp4_image_fetcher.start()

        self.imgViewerControl = TimepixImageControl()
        self.imgViewerControl.updateLevelRange(-10,254+10)
        self.imgViewerControl.frameCounterTool.setMaximum(buffer_size)
        self.imgViewerControl.set_img.connect(self.set_image_from_buffer)
        self.imgViewerControl.histogram_img.connect(self.set_histogram_image)
        self.imgViewerControl.update_image.connect(self.update_image_viewer)
        self.imgViewerControl.update_image_viewer.connect(self.onImageControlChanged)
        self.imgViewerControl.update_image_config.connect(self.update_image_viewer)
        layout.addWidget(self.imgViewerControl)
        window.setLayout(layout)

        self.setCentralWidget(window)

        self.tp_menu_bar = TimepixMenuBar()
        self.tp_menu_bar.saveMatrix.connect(self.saveMatrixConfig)
        self.tp_menu_bar.toggleMatrixConfig.connect(self.toggleMatrixConfig)
        self.tp_menu_bar.saveToFile.connect(self.saveToFile)
        self.tp_menu_bar.loadFromFile.connect(self.loadFromFile)
        self.setMenuBar(self.tp_menu_bar)

    def saveToFile(self, filename):
        xml = timepix_xml()
        xml.add_images_element(self.img_buffer[self.img_buffer_ptr:self.img_buffer_ptr+1])
        xml.write_to_file(filename)

    def loadFromFile(self, filename):
        with open(filename, "r") as f:
            pass
            
    
    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.imgViewer.autoRange()

    def saveMatrixConfig(self, checked):
        pass

    def toggleMatrixConfig(self):
        self.matrixConfig.setVisible(not self.matrixConfig.isVisible())
        if not self.matrixConfig.isVisible():
            self.changeImageMode(ImageModes.Imaging, np.array([]))

    def changeImageMode(self, mode, image):
        self.img_mode = mode
        self.imgViewerControl.updateFrame.setChecked(False)

        if mode == ImageModes.Imaging:
            self.update_image_viewer(self.img_buffer[self.imgViewerControl.frameCounterTool.value()])
        else:
            self.update_image_viewer(image)

    def mouseMoved(self, pos):
        x = int(self.imgViewer.getImageItem().mapFromScene(pos).x())
        y = int(self.imgViewer.getImageItem().mapFromScene(pos).y())
        if x < 0 or y < 0 or x >= len(self.imgViewer.image) or y >= len(self.imgViewer.image[0]):
            return
        count = self.imgViewer.image[x,y]
        self.imgViewerControl.cursorDetails.setCursorHover(x_val=x, y_val=y, count=count)
    
    def mouseClicked(self, event):
        if self.img_mode == ImageModes.Imaging:
            event.ignore()
            return
        
        # Left Mouse Button Controls
        if event.button() == 1:
            pos = event.scenePos()
            x = int(self.imgViewer.getImageItem().mapFromScene(pos).x())
            y = int(self.imgViewer.getImageItem().mapFromScene(pos).y())
            if x < 0 or y < 0 or x >= len(self.imgViewer.image) or y >= len(self.imgViewer.image[0]):
                return
            
            self.matrixConfig.editImage(x, y)


    def set_image_from_buffer(self, index):
        if self.buffer_filled:
            img = self.img_buffer[(index + self.img_buffer_ptr) % self.img_buffer_size]
        else:
            img = self.img_buffer[index]
        
        self.update_image_viewer(img)
            
    
    def set_histogram_image(self, state):
        pass

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
        if img is None:
            return
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
    
    def onImageControlChanged(self, config : ImageViewConfig):
        self.imgViewer.setColorMap(pg.colormap.get(config.colormap.lower(), source=config.colormapSource))


# Menu Bar for the Main Timepix UI.
class TimepixMenuBar(QMenuBar):
    saveMatrix = pyqtSignal(bool)
    loadMatrix = pyqtSignal(bool)
    toggleMatrixConfig = pyqtSignal()
    loadFromFile = pyqtSignal(str)
    saveToFile = pyqtSignal(str)
    fileDialogFilter = "XML File (*.xml);;All Files (*)"
    def __init__(self):
        super(TimepixMenuBar, self).__init__()
        self.create_actions()
        self.create_menu_bar()
    
    def loadFileAction(self):
        name = QtGui.QFileDialog.getOpenFileName(self, 'Load File', filter=self.fileDialogFilter)
        self.loadFromFile.emit(name[0])
        
    def saveFileAction(self):
        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File', filter=self.fileDialogFilter)
        self.saveToFile.emit(name[0])
    
    def create_actions(self):
        #Actions for the File Menu
        self.loadPicture = QAction("&Load Picture...", self)
        self.loadPicture.triggered.connect(self.loadFileAction)
        self.savePicture = QAction("&Save Picture...", self)
        self.savePicture.triggered.connect(self.saveFileAction)
        self.exit = QAction("&Exit", self)

        #Actions for the Options Menu
        self.matrixConfig = QAction("Toggle Matrix Configuration")
        self.matrixConfig.triggered.connect(self.toggleMatrixConfig)
        self.saveMatrixConfig = QAction("&Save Matrix Config", self)
        self.saveMatrix = self.saveMatrixConfig.triggered
        self.loadMatrixConfig = QAction("&Load Matrix Config", self)
        self.loadMatrix = self.loadMatrixConfig.triggered
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

    
    def create_menu_bar(self):
        #Creating File Menu Bar
        fileMenu = self.addMenu("File")
        fileMenu.addAction(self.loadPicture)
        fileMenu.addAction(self.savePicture)
        fileMenu.addAction(self.exit)

        #Creating Options Menu Bar
        optionsMenu = self.addMenu("Options")
        optionsMenu.addAction(self.matrixConfig)
        optionsMenu.addAction(self.saveMatrixConfig)
        optionsMenu.addAction(self.loadMatrixConfig)
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

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.begin = QPoint()
        self.end = QPoint()
        self.ctrlPressed = False
        self.show()

    def paintEvent(self, event):
        qp = QPainter(self)
        br = QBrush(QColor(100, 10, 10, 40))  
        qp.setBrush(br)   
        qp.drawRect(QRect(self.begin, self.end))

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        self.ctrlPressed = True

    def keyReleaseEvent(self, a0: QtGui.QKeyEvent) -> None:
        self.ctrlPressed = False       

    def mousePressEvent(self, event):
        if self.ctrlPressed == False:
            return
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        if self.ctrlPressed == False:
            return
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        if self.ctrlPressed == False:
            return
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    timepixControl = TimepixControl()
    timepixControl.show()
    sys.exit(app.exec_())

