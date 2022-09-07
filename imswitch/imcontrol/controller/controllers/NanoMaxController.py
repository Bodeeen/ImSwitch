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
lr_chan = 1
ud_chan = 0
pm_chan = 2
class NanoMaxControl(QtWidgets.QWidget):

    def __init__(self, port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('NanoMax Stepper motor controller')
        self.dev = BSC(serial_port=port, vid=None, pid=None, manufacturer=None, product=None, serial_number=None,
                       location=None, home=True, x=3, invert_direction_logic=False, swap_limit_switches=True)

        self.initialZPos_mm = 2
        self.getPosUpdateInterv_ms = 500

        self.initVelUD, self.initVelLR, self.initVelPM = 10, 10, 10

        print('Homing devices')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.initialize)
        self.timer.start(15000)

        """GUI elements"""

        self.XYVelLabel = QtWidgets.QLabel('X/Y velocity [um/s]')
        self.XYVelEdit = QtWidgets.QDoubleSpinBox()
        self.XYVelEdit.setMaximum(1000)
        self.XYVelEdit.setMinimum(0)
        self.XYVelEdit.setValue(10)
        self.XYVelEdit.editingFinished.connect(self.setXYVelocity)

        self.ZVelLabel = QtWidgets.QLabel('Z velocity [um/s]')
        self.ZVelEdit = QtWidgets.QDoubleSpinBox()
        self.ZVelEdit.setMaximum(1000)
        self.ZVelEdit.setMinimum(0)
        self.ZVelEdit.setValue(10)
        self.ZVelEdit.editingFinished.connect(self.setZVelocity)

        self.setPosLabel = QtWidgets.QLabel('Set absolute position [um]')

        self.setXLabel = QtWidgets.QLabel('X')
        self.setXEdit = QtWidgets.QDoubleSpinBox()
        self.setYLabel = QtWidgets.QLabel('Y')
        self.setYEdit = QtWidgets.QDoubleSpinBox()
        self.setZLabel = QtWidgets.QLabel('Z')
        self.setZEdit = QtWidgets.QDoubleSpinBox()

        self.moveToBtn = QtWidgets.QPushButton('Move to pos')
        self.moveToBtn.clicked.connect(self.moveTo)

        self.pos0Label = QtWidgets.QLabel('X position [µm]')
        self.pos0EditLabel = QtWidgets.QLabel()
        self.pos1Label = QtWidgets.QLabel('Y position [µm]')
        self.pos1EditLabel = QtWidgets.QLabel()
        self.pos2Label = QtWidgets.QLabel('Z position [µm]')
        self.pos2EditLabel = QtWidgets.QLabel()

        # Add elements to GridLayout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(self.XYVelLabel, 0 ,0, 1, 1)
        grid.addWidget(self.XYVelEdit, 0, 1, 1, 1)
        grid.addWidget(self.ZVelLabel, 1, 0, 1, 1)
        grid.addWidget(self.ZVelEdit, 1, 1, 1, 1)
        grid.addWidget(self.setPosLabel, 2, 0, 1, 2)
        grid.addWidget(self.setXLabel, 3, 0, 1, 1)
        grid.addWidget(self.setXEdit, 3, 1, 1, 1)
        grid.addWidget(self.setYLabel, 4, 0, 1, 1)
        grid.addWidget(self.setYEdit, 4, 1, 1, 1)
        grid.addWidget(self.setZLabel, 5, 0, 1, 1)
        grid.addWidget(self.setZEdit, 5, 1, 1, 1)
        grid.addWidget(self.moveToBtn, 6, 0, 1, 2)
        grid.addWidget(self.pos0Label, 7, 0, 1, 1)
        grid.addWidget(self.pos0EditLabel, 7, 1, 1, 1)
        grid.addWidget(self.pos1Label, 8, 0, 1, 1)
        grid.addWidget(self.pos1EditLabel, 8, 1, 1, 1)
        grid.addWidget(self.pos2Label, 9, 0, 1, 1)
        grid.addWidget(self.pos2EditLabel, 9, 1, 1, 1)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def to_enc_steps(self, mm):
        steps = mm * REV_PER_MM * STEPS_PER_REV
        return int(steps)

    def to_mm(self, steps):
        mm = steps / (REV_PER_MM * STEPS_PER_REV)
        return mm

    def initialize(self):
        print('Setting initial position')
        self.dev.set_velocity_params(acceleration=4506, max_velocity=21987328 * 5, bay=0, channel=0)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=21987328 * 5, bay=1, channel=0)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=21987328 * 5, bay=2, channel=0)
        self.move_relative_mm(self.initialZPos_mm, 2)
        self.timer.timeout.disconnect(self.initialize)
        self.timer.timeout.connect(self.setInitialVelocity)
        self.timer.start(1)

    def setInitialVelocity(self):
        print('Setting initial velocity')
        self.dev.set_velocity_params(acceleration=4506, max_velocity=int((self.initVelUD * 21987328) / 1000), bay=0, channel=0)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=int((self.initVelLR * 21987328) / 1000), bay=1, channel=0)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=int((self.initVelPM * 21987328) / 1000), bay=2, channel=0)
        self.timer.timeout.disconnect(self.setInitialVelocity)
        self.timer.timeout.connect(self.getPosition)
        self.timer.start(self.getPosUpdateInterv_ms)

    def setVelocity(self, um_per_s, axis):
        print('Setting velocity with args ', um_per_s, axis)
        self.dev.set_velocity_params(acceleration=4506, max_velocity=int((um_per_s * 21987328) / 1000), bay=axis, channel=0)

    def setXYVelocity(self):
        um_per_s = self.XYVelEdit.value()

        self.setVelocity(um_per_s, 0)
        self.setVelocity(um_per_s, 1)
        print('Set XY velocity with', um_per_s)

    def setZVelocity(self):
        um_per_s = self.ZVelEdit.value()
        self.setVelocity(um_per_s, 2)

    def moveTo(self):
        pass

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

    def move_constant(self, direction, axis):
        self.dev.move_velocity(direction=direction, bay=axis, channel=0)

    def move_absolute_mm(self, position_mm, axis):
        pos = self.to_enc_steps(position_mm)
        self.dev.move_absolute(pos, now=True, bay=axis, channel=0)

    def stop(self, axis):
        self.dev.stop(bay=axis)


    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() == QtCore.Qt.Key_Right:
                print('Right key pressed')
                self.move_constant(False, lr_chan)
            elif event.key() == QtCore.Qt.Key_Left:
                print('Left key pressed')
                self.move_constant(True, lr_chan)
            elif event.key() == QtCore.Qt.Key_Up:
                print('Up key pressed')
                self.move_constant(True, ud_chan)
            elif event.key() == QtCore.Qt.Key_Down:
                print('Down key pressed')
                self.move_constant(False, ud_chan)
            elif event.key() == QtCore.Qt.Key_Plus:
                print('Plus key pressed')
                self.move_constant(True, pm_chan)
            elif event.key() == QtCore.Qt.Key_Minus:
                print('Minus key pressed')
                self.move_constant(False, pm_chan)


    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            if (event.key() == QtCore.Qt.Key_Right or event.key() == QtCore.Qt.Key_Left):
                print('Right/Left key released')
                self.stop(lr_chan)
            if (event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_Down):
                print('Up/Down key released')
                self.stop(ud_chan)
            if (event.key() == QtCore.Qt.Key_Plus or event.key() == QtCore.Qt.Key_Minus):
                print('Up/Down key released')
                self.stop(pm_chan)

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