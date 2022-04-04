from qtpy import QtCore, QtWidgets

# from imswitch.imcontrol.view import guitools
# from .basewidgets import Widget


class TriggerScopeWidget(QtWidgets.QWidget):
    """ Widget for controlling the parameters of a TriggerScope. """
    sigRunToggled = QtCore.Signal(float)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.quickSetVoltageLabel = QtWidgets.QLabel('Set voltage')
        self.quickSetVoltageLabel.setStyleSheet("font-weight: bold")

        self.voltageLabel = QtWidgets.QLabel("Voltage")
        self.voltageEdit = QtWidgets.QDoubleSpinBox()
        self.voltageEdit.setMinimum(-5)
        self.voltageEdit.setMaximum(5)
        self.voltageEdit.setSingleStep(0.1)

        self.sequenceLabel = QtWidgets.QLabel('Run scan sequence')
        self.sequenceLabel.setStyleSheet("font-weight: bold")

        self.stepSizeLabel = QtWidgets.QLabel("Step size [V]")
        self.stepSizeEdit = QtWidgets.QDoubleSpinBox()
        self.stepSizeEdit.setMinimum(-5)
        self.stepSizeEdit.setSingleStep(0.1)

        self.nrOfStepsLabel = QtWidgets.QLabel("Steps in scan")
        self.nrOfStepsEdit = QtWidgets.QSpinBox()

        self.TTLtimeLabel = QtWidgets.QLabel("TTL time [ms]")
        self.TTLtimeEdit = QtWidgets.QDoubleSpinBox()
        self.TTLtimeEdit.setSingleStep(0.1)


        self.stepTimeLabel = QtWidgets.QLabel("Step time [ms]")
        self.stepTimeEdit = QtWidgets.QDoubleSpinBox()
        self.stepTimeEdit.setSingleStep(0.1)

        self.repLabel = QtWidgets.QLabel("Repetitions")
        self.repEdit = QtWidgets.QSpinBox()

        self.runButton = QtWidgets.QPushButton('Run')
        self.runButton.clicked.connect(self.sigRunToggled.emit)

        #Set widget layout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.quickSetVoltageLabel, 0, 0)
        grid.addWidget(self.voltageLabel, 1, 0)
        grid.addWidget(self.voltageEdit, 1, 1)
        grid.addWidget(self.sequenceLabel, 2, 0)
        grid.addWidget(self.stepSizeLabel, 3, 0)
        grid.addWidget(self.stepSizeEdit, 3, 1)
        grid.addWidget(self.nrOfStepsLabel, 3, 2)
        grid.addWidget(self.nrOfStepsEdit, 3, 3)
        grid.addWidget(self.TTLtimeLabel, 4, 0)
        grid.addWidget(self.TTLtimeEdit, 4, 1)
        grid.addWidget(self.stepTimeLabel, 4, 2)
        grid.addWidget(self.stepTimeEdit, 4, 3)
        grid.addWidget(self.repLabel, 5, 0)
        grid.addWidget(self.repEdit, 5, 1)
        grid.addWidget(self.runButton, 5, 2)

    def action(self):
        self.setVoltage.setSingleStep(float(self.incrementVoltage.text()))


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    wid = TriggerScopeWidget()
    wid.show()
    sys.exit(app.exec_())