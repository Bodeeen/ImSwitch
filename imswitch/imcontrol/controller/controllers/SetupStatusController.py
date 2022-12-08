from thorlabs_apt_device.devices import APTDevice_Motor
from qtpy import QtCore
from ..basecontrollers import ImConWidgetController
from serial.serialutil import SerialException

class SetupStatusController(ImConWidgetController):
    sigViewTiltedCamera = QtCore.Signal()
    sigViewStraightCamera = QtCore.Signal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        flipMirrorCOMs = ('COM21', 'COM22', 'COM23')
        self.tiltedCamName = 'Orca'
        self.straightCamName = 'WidefieldCamera'

        self.flipMirrors = [APTDevice_Motor(serial_port=port) for port in flipMirrorCOMs]

        """Define configurations"""
        # Note, mirror position depends on how they are physically mounted (there are two holders where the arm can be mounted on the flipper)
        wideFieldParamDict = {'Illumination status': 'Widefield',
                              'Detection status': 'Straight',
                              'Flip mirror positions': [False, False, True],
                              'Hot key': QtCore.Qt.Key_1}
        lightSheetParamDict = {'Illumination status': 'Light sheet',
                               'Detection status': 'Tilted',
                               'Flip mirror positions': [True, True, False],
                               'Hot key': QtCore.Qt.Key_2}
        wideFieldIlluminationParamDict = {'Illumination status': 'Widefield',
                                          'Detection status': None,
                                          'Flip mirror positions': [None, False, True],
                                          'Hot key': QtCore.Qt.Key_4}
        lightSheetIlluminationParamDict = {'Illumination status': 'Light sheet',
                                           'Detection status': None,
                                           'Flip mirror positions': [None, True, False],
                                           'Hot key': QtCore.Qt.Key_5}
        straightDetectionParamDict = {'Illumination status': None,
                                      'Detection status': 'Straight',
                                      'Flip mirror positions': [False, None, None],
                                      'Hot key': QtCore.Qt.Key_7}
        tiltedDetectionParamDict = {'Illumination status': None,
                                    'Detection status': 'Tilted',
                                    'Flip mirror positions': [True, None, None],
                                    'Hot key': QtCore.Qt.Key_8}

        self.setupConfigs = {'Widefield imaging': wideFieldParamDict,
                             'Light sheet imaging': lightSheetParamDict,
                             'Widefield illumination': wideFieldIlluminationParamDict,
                             'Light sheet illumination': lightSheetIlluminationParamDict,
                             'Tilted detection': tiltedDetectionParamDict,
                             'Straight detection': straightDetectionParamDict}

        #Connect keyboard/mouse signals
        self._commChannel.sigKeyReleased.connect(self.keyReleased)

        #Set to initial position
        self.setConfig(self.setupConfigs['Widefield imaging'])

    def setConfig(self, configurationPars: dict):

        self.setFlipMirrorPositions(configurationPars['Flip mirror positions'])
        ill = configurationPars['Illumination status']
        det = configurationPars['Detection status']
        if ill:
            self._widget.illuminationStatusLabel.setText(ill)
        if det:
            self._widget.detectionStatusLabel.setText(det)
            if det == 'Tilted':
                self._commChannel.sigSetVisibleLayers.emit((self.tiltedCamName,))
            elif det == 'Straight':
                self._commChannel.sigSetVisibleLayers.emit((self.straightCamName,))

    def setFlipMirrorPositions(self, positionList: list):

        for i, flipMirror in enumerate(self.flipMirrors):
            newPos = positionList[i]
            if not newPos is None:
                flipMirror.move_jog(positionList[i])

    def closeMirrorDevice(self):
        [fm.close() for fm in self.flipMirrors]

    def keyReleased(self, event):
        if not event.isAutoRepeat():
            self._logger.debug('Key release detected')
            for key, item in self.setupConfigs.items():
                if event.key() == item['Hot key']:
                    self.setConfig(item)