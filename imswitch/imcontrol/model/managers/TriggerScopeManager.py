from imswitch.imcommon.model import initLogger
import threading
from imswitch.imcommon.framework import Signal, SignalInterface, Timer, Thread, Worker
from pyvisa.errors import VisaIOError

class TriggerScopeManager(SignalInterface):
    """ For interaction with TriggerScope hardware interfaces. """
    sigScanDone = Signal()
    sigScanStarted = Signal()

    def __init__(self, setupInfo, rs232sManager):
        super().__init__()

        self.__setupInfo = setupInfo
        daqInfo = self.__setupInfo.daq
        self._rs232manager = rs232sManager[
            daqInfo.managerProperties['rs232device']
        ]
        #Set timeout value for reading
        self._rs232manager.setTimeout(10)

        self.__logger = initLogger(self)
        self.send("*")

        self._serialMonitor = SerialMonitor(self._rs232manager, 1)
        self._thread = Thread()
        self._serialMonitor.moveToThread(self._thread)
        self._thread.started.connect(self._serialMonitor.run)
        self._thread.finished.connect(self._serialMonitor.stop)
        self._thread.start()

        self.deviceInfo = {}
        for target in self.__setupInfo.positioners.keys():
            self.setAnalog(target)
        self.__logger.debug('Set device info to: ' + str(self.deviceInfo))
        #Connect signals from serialMonitor
        self._serialMonitor.sigScanDone.connect(self.sigScanDone)
        self._serialMonitor.sigUnknownMessage.connect(self.unknownMsg)

    def __del__(self):
        self._thread.quit()
        self._thread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def unknownMsg(self, msg):
        self.__logger.info(msg)

    def _setParameter(self, parameterName, parameterValue):
        msg = 'PARAMETER,' + parameterName + ',' + str(parameterValue) + '\n'
        self.send(msg)

    def setDACPosition(self, target, position_um):
        voltage = position_um * self.deviceInfo[target]['ConversionFac']
        msg = 'DAC' + str(self.deviceInfo[target]['Channel'])

    def send(self, command):
        self._rs232manager.write(command)

    def runScan(self, analogParameterDict, digitalParameterDict):
        self.__logger.debug('Running scan with analog parameters: ' + str(analogParameterDict) + 'and digital parameters: ' + str(digitalParameterDict))



        self.sigScanStarted.emit()

    def sendAnalog(self, dacLine, value):
        self.send("DAC" + str(dacLine) + "," + str(((value+5)/10)*65535), 0)

    def sendTTL(self, ttlLine, value):
        self.send("TTL" + str(ttlLine) + "," + str(value), 0)

    def setAnalog(self, target):
        dev, chan = self.__setupInfo.getDevice(target).getAnalogChannel().split('/')
        if dev != 'Triggerscope':
            self.__logger.warning('Analog channel of target is not Triggerscope')
            pass
        if chan[0:3] != 'DAC':
            self.__logger.warning('Channel should be specified as "DAC" + Chanel number')
            pass
        chanNr = chan[-1]
        convF = float(self.__setupInfo.positioners[target].managerProperties['conversionFactor'])

        self.deviceInfo[target] = {'Channel': chanNr,
                                   'ConversionFac': convF,
                                   'MinV': float(self.__setupInfo.positioners[target].managerProperties['minVolt']),
                                   'MaxV': float(self.__setupInfo.positioners[target].managerProperties['maxVolt'])}



    """    
    def run_wave(self, dacArray, ttlArray, params):
        command = "PROG_WAVE," + str(params["analogLine"]) + "," + str(params["digitalLine"]) + "," + str(params["length"]) + "," + str(params["trigMode"]) + "," + str(params["delayDAC"]) + "," + str(params["delayTTL"]) + "," + str(params["reps"])
        self.__logger.debug('Sending following command to Triggerscope: %s' % command)
        self.send(command, 1)
        self.__logger.debug('DAC array sent is: %s' % dacArray)
        for x in range(params["length"]):
            command = str(((dacArray[x]+5)/10)*65535) + "," + str(ttlArray[x])
            self.send(command, 0)
            
        self.send("STARTWAVE", 0)
        s = (params['reps']*params['length']*params['delayDAC'] + 100) / 1000
        self.__logger.debug('Sleeping %s seconds: ' % s)
        self.__logger.debug('Setting DAC to: %s' % dacArray[0])
        timer = threading.Timer(s, lambda: self.finalizeScan([1], [dacArray[0]]))
        timer.start()

    def finalizeScan(self, dac_channels, finalVals):
        for i, c in enumerate(dac_channels):
            self.__logger.debug('Setting DAC channel %d to %d' % (c, finalVals[0]))
            self.sendAnalog(c, finalVals[0])

        self.sigScanDone.emit()
    """

class SerialMonitor(Worker):
    sigScanDone = Signal()
    sigUnknownMessage = Signal(str)

    def __init__(self, rs232Manager, updatePeriod):
        super().__init__()

        self._rs232Manager = rs232Manager
        self._updatePeriod = updatePeriod
        self._vtimer = None

    def run(self):
        self._vtimer = Timer()
        self._vtimer.timeout.connect(self.checkSerial)
        self._vtimer.start(self._updatePeriod)

    def stop(self):
        if self._vtimer is not None:
            self._vtimer.stop()
        self._rs232Manager.finalize()

    def checkSerial(self):

        try:
            msg = self._rs232Manager.read(termination='\r\n')
        except VisaIOError:
            msg = None

        #Check content of message
        if msg != None:
            if msg == 'Scan done':
                self.sigScanDone.emit()
            else:
                self.sigUnknownMessage.emit(msg)

