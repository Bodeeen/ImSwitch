from qtpy import QtCore, QtGui, QtWidgets
from .basewidgets import Widget

class SetupStatusWidget(Widget):
    sigKeyReleased = QtCore.Signal(QtGui.QKeyEvent)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Setup status')

        """GUI elements"""

        self.illuminationLabel = QtWidgets.QLabel('Current illumination config:')
        self.illuminationLabel.setFont(QtGui.QFont('Calibri', 14))
        self.illuminationLabel.setStyleSheet("font-weight: bold")
        self.illuminationStatusLabel = QtWidgets.QLabel('')
        self.illuminationStatusLabel.setFont(QtGui.QFont('Calibri', 14))
        self.illuminationStatusLabel.setStyleSheet("font-weight: bold")
        self.detectionLabel = QtWidgets.QLabel('Current detection config:')
        self.detectionLabel.setFont(QtGui.QFont('Calibri', 14))
        self.detectionLabel.setStyleSheet("font-weight: bold")
        self.detectionStatusLabel = QtWidgets.QLabel('')
        self.detectionStatusLabel.setFont(QtGui.QFont('Calibri', 14))
        self.detectionStatusLabel.setStyleSheet("font-weight: bold")

        self.hotKeyInfo = QtWidgets.QLabel('Hot keys for setting status:')
        self.hotKeyInfo.setFont(QtGui.QFont('Calibri', 14))
        self.hotKeyInfo.setStyleSheet("font-weight: bold")
        self.illDetHK1info = QtWidgets.QLabel('Set illumination and detection to straight widefield:')
        self.illDetHK2info = QtWidgets.QLabel('Set illumination and detection to tilted light sheet:')
        self.illHK1info = QtWidgets.QLabel('Set illumination to widefield:')
        self.illHK2info = QtWidgets.QLabel('Set illumination to light sheet:')
        self.detHK1info = QtWidgets.QLabel('Set detection to straight:')
        self.detHK2info = QtWidgets.QLabel('Set detection to tilted:')

        self.illDetHK1 = QtWidgets.QLabel('1')
        self.illDetHK2 = QtWidgets.QLabel('2')
        self.illHK1 = QtWidgets.QLabel('4')
        self.illHK2 = QtWidgets.QLabel('5')
        self.detHK1 = QtWidgets.QLabel('7')
        self.detHK2 = QtWidgets.QLabel('8')

        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.illuminationLabel, 0, 0, 1, 1)
        grid.addWidget(self.illuminationStatusLabel, 0, 1, 1, 1)
        grid.addWidget(self.detectionLabel, 0, 2, 1, 1)
        grid.addWidget(self.detectionStatusLabel, 0, 3, 1, 1)
        grid.addItem(
            QtWidgets.QSpacerItem(40, 20,
                                  QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
            1, 0
        )
        grid.addWidget(self.hotKeyInfo, 2, 0, 1, 2)
        grid.addWidget(self.illDetHK1info, 3, 0, 1, 1)
        grid.addWidget(self.illDetHK1, 3, 1, 1, 1)
        grid.addWidget(self.illDetHK2info, 4, 0, 1, 1)
        grid.addWidget(self.illDetHK2, 4, 1, 1, 1)
        grid.addWidget(self.illHK1info, 5, 0, 1, 1)
        grid.addWidget(self.illHK1, 5, 1, 1, 1)
        grid.addWidget(self.illHK2info, 6, 0, 1, 1)
        grid.addWidget(self.illHK2, 6, 1, 1, 1)
        grid.addWidget(self.detHK1info, 7, 0, 1, 1)
        grid.addWidget(self.detHK1, 7, 1, 1, 1)
        grid.addWidget(self.detHK2info, 8, 0, 1, 1)
        grid.addWidget(self.detHK2, 8, 1, 1, 1)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def keyReleaseEvent(self, event):
        self.sigKeyReleased.emit(event)
