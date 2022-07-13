from qtpy import QtCore, QtWidgets
import pyqtgraph as pg
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class TriggerScopeWidget(Widget):
    """ Widget for controlling the parameters of a TriggerScope. """
    sigRunClicked = QtCore.Signal()
    sigSaveScan = QtCore.Signal()
    sigLoadScan = QtCore.Signal()
    sigSignalParChanged = QtCore.Signal()
    sigSeqTimeParChanged = QtCore.Signal()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        galvoTitle = QtWidgets.QLabel('<h2><strong>Galvo</strong></h2>')
        galvoTitle.setTextFormat(QtCore.Qt.RichText)
        self.quickSetVoltageLabel = QtWidgets.QLabel('Set position')
        self.quickSetVoltageLabel.setStyleSheet("font-weight: bold")

        self.saveGalvoScanBtn = guitools.BetterPushButton('Save Scan')
        self.loadGalvoScanBtn = guitools.BetterPushButton('Load Scan')

        self.positionLabel = QtWidgets.QLabel("Position [nm]")
        self.positionEdit = QtWidgets.QDoubleSpinBox()
        self.positionEdit.setMinimum(-950000)
        self.positionEdit.setMaximum(950000)
        self.positionEdit.setDecimals(0)
        self.positionEdit.setSingleStep(10)

        self.sequenceLabel = QtWidgets.QLabel('Run scan sequence')
        self.sequenceLabel.setStyleSheet("font-weight: bold")

        self.stepSizeLabel = QtWidgets.QLabel("Step size [nm]")
        self.stepSizeEdit = QtWidgets.QDoubleSpinBox()
        self.stepSizeEdit.setMinimum(-950000)
        self.stepSizeEdit.setMaximum(950000)
        self.stepSizeEdit.setDecimals(0)
        self.stepSizeEdit.setSingleStep(10)

        self.nrOfStepsLabel = QtWidgets.QLabel("Steps in scan")
        self.nrOfStepsEdit = QtWidgets.QSpinBox()
        self.nrOfStepsEdit.setMaximum(1000)

        self.TTLtimeLabel = QtWidgets.QLabel("TTL time [ms]")
        self.TTLtimeEdit = QtWidgets.QSpinBox()
        self.TTLtimeEdit.setMaximum(1000)
        self.TTLtimeEdit.setSingleStep(0.1)


        self.stepTimeLabel = QtWidgets.QLabel("Step time [ms]")
        self.stepTimeEdit = QtWidgets.QSpinBox()
        self.stepTimeEdit.setMaximum(1000)
        self.stepTimeEdit.setSingleStep(0.1)

        self.repLabel = QtWidgets.QLabel("Repetitions")
        self.repEdit = QtWidgets.QSpinBox()

        self.saveGalvoScanBtn.clicked.connect(self.sigSaveScan.emit)
        self.loadGalvoScanBtn.clicked.connect(self.sigLoadScan.emit)


        self.runButton = guitools.BetterPushButton('Run')
        self.runButton.clicked.connect(self.sigRunClicked.emit)

        stageTitle = QtWidgets.QLabel('<h2><strong>Stage</strong></h2>')
        stageTitle.setTextFormat(QtCore.Qt.RichText)

        #Set widget layout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(galvoTitle, 0, 0)
        self.grid.addWidget(self.quickSetVoltageLabel, 1, 0)
        self.grid.addWidget(self.saveGalvoScanBtn, 1, 3)
        self.grid.addWidget(self.positionLabel, 2, 0)
        self.grid.addWidget(self.positionEdit, 2, 1)
        self.grid.addWidget(self.loadGalvoScanBtn, 2, 3)
        self.grid.addWidget(self.sequenceLabel, 3, 0)
        self.grid.addWidget(self.stepSizeLabel, 4, 0)
        self.grid.addWidget(self.stepSizeEdit, 4, 1)
        self.grid.addWidget(self.nrOfStepsLabel, 4, 2)
        self.grid.addWidget(self.nrOfStepsEdit, 4, 3)
        self.grid.addWidget(self.TTLtimeLabel, 5, 0)
        self.grid.addWidget(self.TTLtimeEdit, 5, 1)
        self.grid.addWidget(self.stepTimeLabel, 5, 2)
        self.grid.addWidget(self.stepTimeEdit, 5, 3)
        self.grid.addWidget(self.repLabel, 6, 0)
        self.grid.addWidget(self.repEdit, 6, 1)
        self.grid.addWidget(self.runButton, 6, 2)
        self.grid.addWidget(stageTitle, 7, 0)

        self.loadStageScanBtn = guitools.BetterPushButton('Load stage scan')
        self.saveStageScanBtn = guitools.BetterPushButton('Save stage scan')
        self.stageScanBtn = guitools.BetterPushButton('Run stage scan')
        self.dwellTimePar = QtWidgets.QSpinBox()
        self.scanPar = {}

        self.pxParameters = {}
        self.pxParValues = {}

        self.graph = GraphFrame()
        self.graph.setEnabled(False)
        self.graph.setFixedHeight(128)

        self.dwellTimePar.textChanged.connect(self.sigSeqTimeParChanged)


    def setRunButtonChecked(self, checked):
        self.runButton.setEnabled(not checked)
        self.runButton.setCheckable(checked)
        self.runButton.setChecked(checked)

    def action(self):
        self.setVoltage.setSingleStep(float(self.incrementVoltage.text()))


    def initControls(self, positionerNames, TTLDeviceNames, TTLTimeUnits):
        currentRow = 8
        self.scanDims = positionerNames

        # Add general buttons
        self.grid.addWidget(self.loadStageScanBtn, currentRow, 0)
        self.grid.addWidget(self.saveStageScanBtn, currentRow, 1)
        self.grid.addItem(
            QtWidgets.QSpacerItem(40, 20,
                                  QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum),
            currentRow, 4
        )
        self.grid.addWidget(self.stageScanBtn, currentRow, 3)
        currentRow += 1

        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 40,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )
        currentRow += 1

        # Add param labels
        sizeLabel = QtWidgets.QLabel('Size (µm)')
        stepLabel = QtWidgets.QLabel('Step size (µm)')
        pixelsLabel = QtWidgets.QLabel('Pixels (#)')
        centerLabel = QtWidgets.QLabel('Center (µm)')
        scandimLabel = QtWidgets.QLabel('Scan dim')
        sizeLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        stepLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        pixelsLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        centerLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        scandimLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(sizeLabel, currentRow, 1)
        self.grid.addWidget(stepLabel, currentRow, 2)
        self.grid.addWidget(pixelsLabel, currentRow, 3)
        self.grid.addWidget(centerLabel, currentRow, 4)
        self.grid.addWidget(scandimLabel, currentRow, 6)
        currentRow += 1

        for index, positionerName in enumerate(positionerNames):
            # Scan params
            sizePar = QtWidgets.QLineEdit('2')
            self.scanPar['size' + positionerName] = sizePar
            stepSizePar = QtWidgets.QLineEdit('1')
            self.scanPar['stepSize' + positionerName] = stepSizePar
            numPixelsPar = QtWidgets.QLineEdit('2')
            numPixelsPar.setEnabled(False)
            self.scanPar['pixels' + positionerName] = numPixelsPar
            centerPar = QtWidgets.QLineEdit('0')
            self.scanPar['center' + positionerName] = centerPar
            self.grid.addWidget(QtWidgets.QLabel(positionerName), currentRow, 0)
            self.grid.addWidget(sizePar, currentRow, 1)
            self.grid.addWidget(stepSizePar, currentRow, 2)
            self.grid.addWidget(numPixelsPar, currentRow, 3)
            self.grid.addWidget(centerPar, currentRow, 4)

            # Scan dimension label and pickier
            dimlabel = QtWidgets.QLabel(
                f'{index + 1}{guitools.ordinalSuffix(index + 1)} dimension:'
            )
            dimlabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.grid.addWidget(dimlabel, currentRow, 5)
            scanDimPar = QtWidgets.QComboBox()
            scanDimPar.addItems(self.scanDims)
            scanDimPar.setCurrentIndex(index)
            self.scanPar['scanDim' + str(index)] = scanDimPar
            self.grid.addWidget(scanDimPar, currentRow, 6)

            currentRow += 1

            # Connect signals
            """
            self.scanPar['size' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['stepSize' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['pixels' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['center' + positionerName].textChanged.connect(self.sigStageParChanged)
            self.scanPar['scanDim' + str(index)].currentIndexChanged.connect(
                self.sigStageParChanged
            )
            """

        # Add dwell time parameter
        self.grid.addWidget(QtWidgets.QLabel('Dwell time (ms):'), currentRow, 5)
        self.grid.addWidget(self.dwellTimePar, currentRow, 6)

        # Add space item to make the grid look nicer
        self.grid.addItem(
            QtWidgets.QSpacerItem(20, 40,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            currentRow, 0, 1, -1
        )
        currentRow += 1
        graphRow = currentRow

        # TTL pulse param labels
        startLabel = QtWidgets.QLabel(f'Start ({TTLTimeUnits})')
        endLabel = QtWidgets.QLabel(f'End ({TTLTimeUnits})')
        startLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        endLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.grid.addWidget(startLabel, currentRow, 1)
        self.grid.addWidget(endLabel, currentRow, 2)
        currentRow += 1

        for deviceName in TTLDeviceNames:
            # TTL pulse params
            self.grid.addWidget(QtWidgets.QLabel(deviceName), currentRow, 0)
            self.pxParameters['sta' + deviceName] = QtWidgets.QLineEdit('')
            self.pxParameters['end' + deviceName] = QtWidgets.QLineEdit('')
            self.grid.addWidget(self.pxParameters['sta' + deviceName], currentRow, 1)
            self.grid.addWidget(self.pxParameters['end' + deviceName], currentRow, 2)
            currentRow += 1

            # Connect signals
            self.pxParameters['sta' + deviceName].textChanged.connect(self.sigSignalParChanged)
            self.pxParameters['end' + deviceName].textChanged.connect(self.sigSignalParChanged)


        # Add pulse graph
        self.grid.addWidget(self.graph, graphRow, 3, currentRow - graphRow, 5)

    def plotSignalGraph(self, areas, signals, colors):
        if len(areas) != len(signals) or len(signals) != len(colors):
            raise ValueError('Arguments "areas", "signals" and "colors" must be of equal length')

        self.graph.plot.clear()
        for i in range(len(areas)):
            self.graph.plot.plot(areas[i], signals[i], pen=pg.mkPen(colors[i]))

        self.graph.plot.setYRange(-0.1, 1.1)

class GraphFrame(pg.GraphicsLayoutWidget):
    """Creates the plot that plots the preview of the pulses."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot = self.addPlot(row=1, col=0)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    wid = TriggerScopeWidget()
    wid.show()
    sys.exit(app.exec_())