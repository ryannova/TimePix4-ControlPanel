from PyQt5.QtWidgets import QFrame

HEADER_SIZE = 4
FRAME_SIZE = 128*128
PACKET_SIZE = HEADER_SIZE + FRAME_SIZE

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

class ImageModes():
    Imaging = 1
    Mask = 2
    Test = 3
    THL = 4

# Defining the different types of control modes within a certain image.
class ImageControlModes():
    Point = 1
    Row = 2
    Column = 3
    Area = 4
