from imswitch.imcommon.model import initLogger
import threading
from imswitch.imcommon.framework import Signal, SignalInterface, Timer, Thread, Worker

class TriggerScopeManager(SignalInterface):
    """ For interaction with TriggerScope hardware interfaces. """
    sigScanDone = Signal()

    def __init__(self, daqInfo, **lowLevelManagers):
        super().__init__()
        self._rs232manager = lowLevelManagers['rs232sManager'][
            daqInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self)
        self.__logger.info(self.send("*", 1))

        self._serialMonitor = SerialMonitor(self._rs232manager, 1)
        self._thread = Thread()
        self._serialMonitor.moveToThread(self._thread)
        self._thread.started.connect(self._serialMonitor.run)
        self._thread.finished.connect(self._serialMonitor.stop)
        self._thread.start()
        
        #Connect signals from serialMonitor
        self._serialMonitor.sigScanDone.connect(self.scanDone)

    def __del__(self):
        self._thread.quit()
        self._thread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def send(self, command, recieve):  
        if recieve:
            return self._rs232manager.query(command)
        else:
            self._rs232manager.write(command)
        
    def sendAnalog(self, dacLine, value):
        self.send("DAC" + str(dacLine) + "," + str(((value+5)/10)*65535), 0)

    def sendTTL(self, ttlLine, value):
        self.send("TTL" + str(ttlLine) + "," + str(value), 0)
        
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


class SerialMonitor(Worker):
    sigScanDone = Signal()
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

    def checkSerial(self):

        msg = self._rs232Manager.read()
        #Check content of message
        if msg == 'Scan done':
            self.sigScanDone.emit()

