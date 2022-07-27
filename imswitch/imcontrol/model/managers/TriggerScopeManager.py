from imswitch.imcommon.model import initLogger
import numpy as np
from imswitch.imcommon.framework import Signal, SignalInterface, Timer, Thread, Worker
from pyvisa.errors import VisaIOError, InvalidSession
import time

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
        self._rs232manager.setTimeout(100000)

        self.__logger = initLogger(self)
        self.send("*")

        self._serialMonitor = SerialMonitor(self._rs232manager, 5)
        self._thread = Thread()
        self._serialMonitor.moveToThread(self._thread)
        self._thread.started.connect(self._serialMonitor.run)
        self._thread.finished.connect(self._serialMonitor.stop)
        self._thread.start()

        self._deviceInfo = {}
        self.__logger.debug('All devices: ' + str(setupInfo.getAllDevices()))
        for targetName, targetInfo in setupInfo.getAllDevices().items():
            analogChannel = targetInfo.getAnalogChannel()
            digitalLine = targetInfo.getDigitalLine()
            if analogChannel is not None:
                dev, chan = analogChannel.split('/')
                if dev == 'Triggerscope' and chan[0:3] == 'DAC':
                    chanNr = chan[-1]
                    self._deviceInfo.update({targetName: {'DACChannel': chanNr,
                                                          'MinV': targetInfo.managerProperties['minVolt'],
                                                          'MaxV': targetInfo.managerProperties['maxVolt']}})
            if digitalLine is not None:
                dev, line = digitalLine.split('/')
                if dev == 'Triggerscope' and line[0:3] == 'TTL':
                    lineNr = line[-1]
                    if targetName in self._deviceInfo.keys():
                        self._deviceInfo[targetName].update({'TTLLine': lineNr})
                    else:
                        self._deviceInfo.update({targetName: {'TTLLine': lineNr}})

        #Connect signals from serialMonitor
        self._serialMonitor.sigScanDone.connect(self.sigScanDone)
        self._serialMonitor.sigUnknownMessage.connect(self.unknownMsg)

    def __del__(self):
        self._thread.quit()
        self._thread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def unknownMsg(self, msg):
        self.__logger.info('[Triggerscope serial] ' + msg)

    def setParameter(self, parameterName, parameterValue):
        msg = 'PARAMETER,' + parameterName + ',' + str(parameterValue) + '\n'
        self.send(msg)

    def send(self, command):
        self._rs232manager.write(command)

    def runScan(self, parameterDict, type=None):
        self.__logger.debug('Running scan with parameters: ' + str(parameterDict))

        if type == 'rasterScan':
            self.runRasterScan(parameterDict)
        else:
            self.__logger.info('Unknown scan type')

    def runRasterScan(self, rasterScanParameters):
        sleepTime = 0.05
        seqTime = rasterScanParameters['Digital']['sequence_time']
        self.setParameter('sequenceTimeUs', int(seqTime * 1e6))
        time.sleep(sleepTime)

        startTimes = rasterScanParameters['Digital']['TTL_start']
        if len(startTimes) > 0:
            endTimes = rasterScanParameters['Digital']['TTL_end']
            firstStart = np.min(startTimes)
            firstIndex = startTimes.index(firstStart)
            endOfPulse = endTimes[firstIndex]
            firstPulseTarget = rasterScanParameters['Digital']['target_device'][firstIndex]
            firstPulseLine = self._deviceInfo[firstPulseTarget]['TTLLine']

            self.setParameter('p1Line', int(firstPulseLine))
            time.sleep(sleepTime)
            self.setParameter('p1StartUs', int(firstStart * 1e6))
            time.sleep(sleepTime)
            self.setParameter('p1EndUs', int(endOfPulse * 1e6))
            time.sleep(sleepTime)

        self.__logger.debug('Setting parameters')
        try:
            chan = self._deviceInfo[rasterScanParameters['Analog']['targets'][0]]['DACChannel']
            self.setParameter('dimOneChan', chan)
            time.sleep(sleepTime)
            self.setParameter('dimOneStartV', rasterScanParameters['Analog']['startPos'][0])
            time.sleep(sleepTime)
            self.setParameter('dimOneLenV', rasterScanParameters['Analog']['lengths'][0])
            time.sleep(sleepTime)
            self.setParameter('dimOneStepSizeV', rasterScanParameters['Analog']['stepSizes'][0])
            time.sleep(sleepTime)
        except IndexError:
            pass
        try:
            chan = self._deviceInfo[rasterScanParameters['Analog']['targets'][1]]['DACChannel']
            self.setParameter('dimTwoChan', chan)
            time.sleep(sleepTime)
            self.setParameter('dimTwoStartV', rasterScanParameters['Analog']['startPos'][1])
            time.sleep(sleepTime)
            self.setParameter('dimTwoLenV', rasterScanParameters['Analog']['lengths'][1])
            time.sleep(sleepTime)
            self.setParameter('dimTwoStepSizeV', rasterScanParameters['Analog']['stepSizes'][1])
            time.sleep(sleepTime)
        except IndexError:
            pass
        try:
            chan = self._deviceInfo[rasterScanParameters['Analog']['targets'][2]]['DACChannel']
            self.setParameter('dimThreeChan', chan)
            time.sleep(sleepTime)
            self.setParameter('dimThreeStartV', rasterScanParameters['Analog']['startPos'][2])
            time.sleep(sleepTime)
            self.setParameter('dimThreeLenV', rasterScanParameters['Analog']['lengths'][2])
            time.sleep(sleepTime)
            self.setParameter('dimThreeStepSizeV', rasterScanParameters['Analog']['stepSizes'][2])
            time.sleep(sleepTime)
        except IndexError:
            pass
        try:
            chan = self._deviceInfo[rasterScanParameters['Analog']['targets'][3]]['DACChannel']
            self.setParameter('dimFourChan', chan)
            time.sleep(sleepTime)
            self.setParameter('dimFourStartV', rasterScanParameters['Analog']['startPos'][3])
            time.sleep(sleepTime)
            self.setParameter('dimFourLenV', rasterScanParameters['Analog']['lengths'][3])
            time.sleep(sleepTime)
            self.setParameter('dimFourStepSizeV', rasterScanParameters['Analog']['stepSizes'][3])
            time.sleep(sleepTime)
        except IndexError:
            pass
        self.setParameter('angleRad', np.deg2rad(0))
        time.sleep(sleepTime)
        self.__logger.debug('Parameters set')

        self.send('RASTER_SCAN')

        self.sigScanStarted.emit()

    def sendAnalog(self, dacLine, value):
        self.send("DAC" + str(dacLine) + "," + str(((value+5)/10)*65535), 0)

    def sendTTL(self, ttlLine, value):
        self.send("TTL" + str(ttlLine) + "," + str(value), 0)

    def setDigital(self, target, booleanValue):
        msg = 'TTL' + str(self._deviceInfo[target]['Channel']) + ',' + str(booleanValue)
        self.send(msg)

    def setAnalog(self, target, voltage):

        if self._deviceInfo[target]['MinV'] <= voltage <= self._deviceInfo[target]['MaxV']:
            msg = 'DAC' + str(self._deviceInfo[target]['DACChannel']) + ',' + str(voltage)
            self.send(msg)
        else:
            self.__logger.warning('Trying to set Triggerscope voltage outside allowed range')



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
        except InvalidSession:
            msg = None

        #Check content of message
        if msg != None:
            if msg == 'Scan done':
                self.sigScanDone.emit()
            else:
                self.sigUnknownMessage.emit(msg)

