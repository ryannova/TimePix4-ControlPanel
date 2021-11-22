from PyQt5.QtCore import QLine, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDropEvent
from PyQt5.QtCore import QThread, pyqtSignal
import sys
from timepix_utils import *

VARIABLES = ["IKrum", "Disc", "Preamp", "BuffAnalogA", "BuffAnalogB", "Hist", "THL", "THLCoarse", "Vcas", "FBK", "GND", "THS", "BiasVDS", "ReflVDS", "ExtDAC"]


class VariableControl(QWidget):
    def __init__(self, label : str = ""):
        super(VariableControl, self).__init__()
        self.label_str = label
        if self.label_str == '':
            self.label_str = "Variable Name"
        self.main_layout = QVBoxLayout()
        
        self.setup()

    def setup(self):
        self.label = QLabel(self.label_str)
        self.main_layout.addWidget(self.label)

        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Vertical)
        self.slider.setMaximum(255)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.main_layout.addWidget(self.slider)

        self.spin_box = QSpinBox()
        self.spin_box.setMaximum(255)
        self.spin_box.setMinimum(0)
        self.spin_box.valueChanged.connect(self.spin_box_value_changed)
        self.main_layout.addWidget(self.spin_box)

        self.locked = QCheckBox("Locked")
        self.locked.stateChanged.connect(self.lock_state_changed)
        self.main_layout.addWidget(self.locked)

        self.setLayout(self.main_layout)

    
    def spin_box_value_changed(self, value):
        self.slider.setValue(value)

    def slider_value_changed(self, value):
        self.spin_box.setValue(value)

    def lock_state_changed(self, state):
        self.slider.setDisabled(state)
        self.spin_box.setDisabled(state)

class VariableControlArray(QWidget):
    def __init__(self, labels : list = []):
        super(VariableControlArray, self).__init__()
        self.variable_array = []
        self.main_layout = QHBoxLayout()

        self.add_variables(labels=labels)

        self.setLayout(self.main_layout)

    def add_variable(self, label : str):
        new_variable = VariableControl(label=label)
        self.main_layout.addWidget(new_variable)
        self.variable_array.append(new_variable)
    
    def add_variables(self, labels : list):
        for l in labels:
            self.add_variable(label=l)

class ChipControl(QWidget):
    def __init__(self):
        super(ChipControl, self).__init__()

        self.main_layout = QVBoxLayout()
        self.chip_number = 1
        self.ext_DAC = "None"

        self.setup()

        self.setLayout(self.main_layout)

    def setup(self):
        chip_layout = QHBoxLayout()
        chip_layout.addWidget(QLabel("Chip number:"))
        self.chip_number_box = QComboBox()
        self.chip_number_box.addItem("1")
        self.chip_number_box.addItem("2")
        self.chip_number_box.addItem("3")
        chip_layout.addWidget(self.chip_number_box)
        self.main_layout.addLayout(chip_layout)

        ext_DAC_layout = QHBoxLayout()
        ext_DAC_layout.addWidget(QLabel("Ext. DAC:"))
        self.ext_DAC_box = QComboBox()
        self.ext_DAC_box.addItem("None")
        ext_DAC_layout.addWidget(self.ext_DAC_box)
        self.main_layout.addLayout(ext_DAC_layout)

        self.main_layout.addWidget(QLabel("Effective Threshold"))

        self.main_layout.addWidget(QHLine())

        self.main_layout.addWidget(QLabel("THL-FBK:"))
        self.THL_FBK = QLabel("-")
        self.main_layout.addWidget(self.THL_FBK)

        self.main_layout.addWidget(QLabel("THH-FBK:"))
        self.THH_FBK = QLabel("-")
        self.main_layout.addWidget(self.THH_FBK)

        self.main_layout.addWidget(QHLine())

        self.settings_button = QPushButton("Settings")
        self.main_layout.addWidget(self.settings_button)


class Timepix4DACControl(QMainWindow):
    def __init__(self):
        super(Timepix4DACControl, self).__init__()
        self.setWindowTitle("DAC Control Panel")
        self.resize(1200,300)

        self.central_widget = QWidget()
        self.central_layout = QHBoxLayout()

        self.chip_control = ChipControl()
        self.central_layout.addWidget(self.chip_control)

        self.central_layout.addWidget(QVLine())

        self.variable_array = VariableControlArray(labels=VARIABLES)
        self.central_layout.addWidget(self.variable_array)


        self.central_widget.setLayout(self.central_layout)

        self.setCentralWidget(self.central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    timepixControl = Timepix4DACControl()
    timepixControl.show()
    sys.exit(app.exec_())