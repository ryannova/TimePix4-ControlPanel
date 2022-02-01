from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import *
from pyqtgraph.graphicsWindows import ImageWindow

from timepix_utils import *

class ImageModes():
    Imaging = 1
    Mask = 2
    Test = 3
    THL = 4

# Defining the different types of control modes within a certain image.
class ImageEditModes():
    Point = 1
    Row = 2
    Column = 3
    Area = 4

# TimepixImageTabs generates and monitor tabs for the Image Viewer.
# Allows user the cycle between different imaging tabs for setting certain 
# frames such as mask and thl.
class TimepixImageTabs(QWidget):
    modeChanged = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.imageMode = ImageModes.Imaging
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
        self.imageMode = ImageModes.Imaging
        self.checkedButton.setChecked(False)
        self.checkedButton = self.frameButton
        self.modeChanged.emit(ImageModes.Imaging)

    def maskPressed(self):
        self.imageMode = ImageModes.Mask
        self.checkedButton.setChecked(False)
        self.checkedButton = self.maskButton
        self.modeChanged.emit(ImageModes.Mask)

    def testPressed(self):
        self.imageMode = ImageModes.Test
        self.checkedButton.setChecked(False)
        self.checkedButton = self.testButton
        self.modeChanged.emit(ImageModes.Test)

    def thlPressed(self):
        self.imageMode = ImageModes.THL
        self.checkedButton.setChecked(False)
        self.checkedButton = self.thlButton
        self.modeChanged.emit(ImageModes.THL)
    
# Main Control of the Timepix Image Viewer
class TimepixImageEditControls(QWidget):
    modeChanged = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.editMode = ImageEditModes.Point
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
        self.editMode = ImageEditModes.Point
        self.modeChanged.emit(ImageEditModes.Point)

    def columnPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.columnButton
        self.editMode = ImageEditModes.Column
        self.modeChanged.emit(ImageEditModes.Column)

    def rowPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.rowButton
        self.editMode = ImageEditModes.Row
        self.modeChanged.emit(ImageEditModes.Row)

    def areaPressed(self):
        self.checkedButton.setChecked(False)
        self.checkedButton = self.areaButton
        self.editMode = ImageEditModes.Area
        self.modeChanged.emit(ImageEditModes.Area)

class TimepixMatrixConfig(QWidget):
    imageChanged = pyqtSignal(int, np.ndarray)
    def __init__(self) -> None:
        self.testImage = np.zeros(IMAGESIZE)
        self.maskImage = np.zeros(IMAGESIZE)
        self.thlImage = np.zeros(IMAGESIZE)
        super().__init__()

        widgetLayout = QVBoxLayout()
        
        self.imageTabs = TimepixImageTabs()
        self.imageTabs.modeChanged.connect(self.changeMode)
        widgetLayout.addWidget(self.imageTabs)

        self.imageEditControls = TimepixImageEditControls()
        widgetLayout.addWidget(self.imageEditControls)

        self.setLayout(widgetLayout)
    
    def setEditControlsVisible(self, value):
        self.imageEditControls.setVisible(value)
    
    def setEditMode(self, value):
        self.imageEditControls.editMode = value
    
    def getImageMode(self):
        return self.imageTabs.imageMode

    def getEditMode(self):
        return self.imageEditControls.editMode
    
    def getEditArea(self):
        return self.imageEditControls.areaRow.value(), self.imageEditControls.areaRow.value()
    
    def changeMode(self, mode):
        if mode == ImageModes.Imaging:
            self.setEditControlsVisible(False)
            self.imageChanged.emit(mode, np.array([]))
        elif mode == ImageModes.Mask:
            self.setEditControlsVisible(True)
            self.imageChanged.emit(mode, self.maskImage)
        elif mode == ImageModes.Test:
            self.setEditControlsVisible(True)
            self.imageChanged.emit(mode, self.testImage)
        elif mode == ImageModes.THL:
            self.setEditControlsVisible(True)
            self.imageChanged.emit(mode, self.thlImage)
    
    def editImage(self, row, col):
        image = np.array([])
        if self.getImageMode() == ImageModes.Imaging:
            self.imageChanged.emit(self.getImageMode(), None)
            return
        elif self.getImageMode() == ImageModes.Mask:
            image = self.maskImage
        elif self.getImageMode() == ImageModes.Test:
            image = self.testImage
        elif self.getImageMode() == ImageModes.THL:
            image = self.thlImage
        else:
            return
        
        if self.getEditMode() == ImageEditModes.Point:
            image[row, col] = 1
        elif self.getEditMode() == ImageEditModes.Row:
            image[:, col] = np.ones(IMAGESIZE[0])
        elif self.getEditMode() == ImageEditModes.Column:
            image[row, :] = np.ones(IMAGESIZE[1])
        elif self.getEditMode() == ImageEditModes.Area:
            boxRow, boxCol = self.getEditArea()
            image[row : row+int(boxRow), col : col+int(boxCol)] = np.ones((boxRow, boxCol))

        self.imageChanged.emit(self.getImageMode(), image)
 