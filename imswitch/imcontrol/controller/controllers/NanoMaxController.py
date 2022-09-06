from thorlabs_apt_device.devices.bsc import BSC
from qtpy import QtCore, QtWidgets
import time
"""
Windows Only: Enable Virtual COM Port¶
On Windows, the virtual serial communications port (VCP) may need to be enabled in the driver options for the USB 
interface device. First, open the Windows Device Manager. If plugging in the controller causes a new COM device to 
appear under the “Ports (COM & LPT)” section, then there is nothing more to do. If a new COM device does not appear, 
then find the controller device under “Universal Serial Bus Controllers”, it may be called “Thorlabs APT Controller” 
or similar (see what new device appears when plugging in the controller). Right-click->Properties->Advanced tab, check 
the “Load VCP” box, then OK out of the dialog back to the device manager. Unplug and re-plug the USB connection to the 
controller, and ensure than a new COM device now appears.
"""

"""
Note that the bay-type devices such as BBD and BSCs are referred to as a x-channel controllers, but the actual device 
layout is that the controller is a “rack” system with three bays, where x number of single-channel controller cards may 
be installed. In other words, the BBD203 “3 channel” controller actually has 3 populated bays 
(bays=(EndPoint.BAY0, EndPoint.BAY1, EndPoint.BAY2)), each of which only controls a single channel (channels=(1,)).
"""


"""
How to calculate the linear displacement per microstep
The stepper motor used in the DRV001 actuator has 200 full steps per revolution of the motor. Each full step is broken down into 2048 microsteps. There are
409,600 microsteps per revolution of the motor when using the BSC201 controller. The end result is the leadscrew advances by 0.5 mm. To calculate the linear
displacement of the actuator microstep, use the following:
409,600 microsteps per revolution of the lead screw
The linear displacement of the lead screw per microstep is:
0.5 mm / 409,600 = 1.2 x 10-6 mm
To calculate the linear displacment for a full step, substitute 409,600 with 200.
"""

STEPS_PER_REV = 409600
REV_PER_MM = 2


move_step_mm = 1
lr_chan = 0
ud_chan = 1
pm_chan = 2
class NanoMaxControl(QtWidgets.QWidget):

    def __init__(self, port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('NanoMax Stepper motor controller')
        self.dev = BSC(serial_port=port, vid=None, pid=None, manufacturer=None, product=None, serial_number=None,
                       location=None, home=True, x=3, invert_direction_logic=False, swap_limit_switches=True)

        self.initialZPos_mm = 2
        self.getPosUpdateInterv_ms = 500
        """GUI elements"""

        self.jogStepLabel = QtWidgets.QLabel('Set jog step size [µm]')
        self.jogStepEdit = QtWidgets.QDoubleSpinBox()
        self.jogStepEdit.setMaximum(1000)
        self.jogStepEdit.setMinimum(0)
        self.jogStepEdit.setValue(5)
        self.jogStepEdit.editingFinished.connect(self.setJogPars)

        self.jogAccLabel = QtWidgets.QLabel('Set jog acceleration [mm/s^2]')
        self.jogAccEdit = QtWidgets.QDoubleSpinBox()
        self.jogAccEdit.setMaximum(10)
        self.jogAccEdit.setMinimum(0)
        self.jogAccEdit.setValue(2)
        self.jogAccEdit.editingFinished.connect(self.setJogPars)

        self.jogMaxVLabel = QtWidgets.QLabel('Set jog max velocity [mm/s]')
        self.jogMaxVEdit = QtWidgets.QDoubleSpinBox()
        self.jogMaxVEdit.setMaximum(100)
        self.jogMaxVEdit.setMinimum(0)
        self.jogMaxVEdit.setValue(10)
        self.jogMaxVEdit.editingFinished.connect(self.setJogPars)

        self.pos0Label = QtWidgets.QLabel('X position [µm]')
        self.pos0EditLabel = QtWidgets.QLabel()
        self.pos1Label = QtWidgets.QLabel('Y position [µm]')
        self.pos1EditLabel = QtWidgets.QLabel()
        self.pos2Label = QtWidgets.QLabel('Z position [µm]')
        self.pos2EditLabel = QtWidgets.QLabel()

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.jogStepLabel, 0 ,0, 1, 1)
        grid.addWidget(self.jogStepEdit, 0, 1, 1, 1)
        grid.addWidget(self.jogAccLabel, 1, 0, 1, 1)
        grid.addWidget(self.jogAccEdit, 1, 1, 1, 1)
        grid.addWidget(self.jogMaxVLabel, 2, 0, 1, 1)
        grid.addWidget(self.jogMaxVEdit, 2, 1, 1, 1)
        grid.addWidget(self.pos0Label, 3, 0, 1, 1)
        grid.addWidget(self.pos0EditLabel, 3, 1, 1, 1)
        grid.addWidget(self.pos1Label, 4, 0, 1, 1)
        grid.addWidget(self.pos1EditLabel, 4, 1, 1, 1)
        grid.addWidget(self.pos2Label, 5, 0, 1, 1)
        grid.addWidget(self.pos2EditLabel, 5, 1, 1, 1)


        print('Homing devices')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.setInitialPos)
        self.timer.start(15000)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setJogPars()

    def to_enc_steps(self, mm):
        steps = mm * REV_PER_MM * STEPS_PER_REV
        return int(steps)

    def to_mm(self, steps):
        mm = steps / (REV_PER_MM * STEPS_PER_REV)
        return mm

    def setInitialPos(self):
        print('Setting initial position')
        self.move_relative_mm(self.initialZPos_mm, 2)
        self.timer.timeout.disconnect(self.setInitialPos)
        self.timer.timeout.connect(self.getPosition)
        self.timer.start(self.getPosUpdateInterv_ms)

    def getPosition(self):
        x, y, z = self.to_mm(self.dev.status_[0][0]['position']), \
                  self.to_mm(self.dev.status_[1][0]['position']), \
                  self.to_mm(self.dev.status_[2][0]['position'])

        self.pos0EditLabel.setText(str(x*1000))
        self.pos1EditLabel.setText(str(y*1000))
        self.pos2EditLabel.setText(str(z*1000))

    def setJogPars(self):
        size_mm = self.jogStepEdit.value() / 1000
        acc_mm = self.jogAccEdit.value()
        maxV_mm = self.jogMaxVEdit.value()
        for b in range(3):
            self.dev.set_jog_params(self.to_enc_steps(size_mm),
                                    self.to_enc_steps(acc_mm),
                                    self.to_enc_steps(maxV_mm),
                                    continuous=False,
                                    immediate_stop=False,
                                    bay=b,
                                    channel=0)

    def jog(self, direction, axis):
        self.dev.move_jog(direction=direction, bay=axis, channel=0)

    def move_relative_mm(self, distance_mm, axis):
        steps = self.to_enc_steps(distance_mm)
        self.dev.move_relative(steps, now=True, bay=axis, channel=0)

    def move_absolute_mm(self, position_mm, axis):
        pos = self.to_enc_steps(position_mm)
        self.dev.move_absolute(pos, now=True, bay=axis, channel=0)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Right:
            print('Right key pressed')
            self.jog(False, ud_chan)
        elif event.key() == QtCore.Qt.Key_Left:
            print('Left key pressed')
            self.jog(True, ud_chan)
        elif event.key() == QtCore.Qt.Key_Up:
            print('Up key pressed')
            self.jog(True, lr_chan)
        elif event.key() == QtCore.Qt.Key_Down:
            print('Down key pressed')
            self.jog(False, lr_chan)
        elif event.key() == QtCore.Qt.Key_Plus:
            print('Plus key pressed')
            self.jog(True, pm_chan)
        elif event.key() == QtCore.Qt.Key_Minus:
            print('Minus key pressed')
            self.jog(False, pm_chan)

    # def keyPressEvent(self, event):
    #     if event.key() == QtCore.Qt.Key_Right:
    #         print('Right key pressed')
    #         self.move_relative_mm(move_step_mm, lr_chan)
    #     elif event.key() == QtCore.Qt.Key_Left:
    #         print('Left key pressed')
    #         self.move_relative_mm(-move_step_mm, lr_chan)
    #     elif event.key() == QtCore.Qt.Key_Up:
    #         print('Up key pressed')
    #         self.move_relative_mm(move_step_mm, ud_chan)
    #     elif event.key() == QtCore.Qt.Key_Down:
    #         print('Down key pressed')
    #         self.move_relative_mm(-move_step_mm, ud_chan)
    #     elif event.key() == QtCore.Qt.Key_Plus:
    #         print('Plus key pressed')
    #         self.move_relative_mm(move_step_mm, pm_chan)
    #     elif event.key() == QtCore.Qt.Key_Minus:
    #         print('Minus key pressed')
    #         self.move_relative_mm(-move_step_mm, pm_chan)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    wid = NanoMaxControl('COM21')
    wid.show()
    sys.exit(app.exec_())