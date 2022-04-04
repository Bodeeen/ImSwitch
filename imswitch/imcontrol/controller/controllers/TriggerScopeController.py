from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
import numpy as np


class TriggerScopeController(ImConWidgetController):
    """ Linked to TriggerScopeWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Connect PositionerWidget signals
        self._widget.sigRunToggled.connect(self.run)
        self._widget.voltageEdit.valueChanged.connect(self.changeVoltag)

    def changeVoltag(self, newV):
        self._master.triggerScopeManager.sendAnalog(1, newV)

    def run(self):
        currentV = self._widget.voltageEdit.value()
        stepsSize = self._widget.stepSizeEdit.value()
        steps = self._widget.nrOfStepsEdit.value()
        finalV = currentV + steps * stepsSize
        dacarray = np.linspace(currentV, finalV, steps)
        ttlarray = np.ones(steps, dtype=int)

        stepTime = self._widget.stepTimeEdit.value()
        TTLTile = self._widget.TTLTimeEdit.value()
        repetitions = self._widget.repEdit
        params = self.setParams(1, 1, len(dacarray), 0, stepTime, TTLTile, repetitions)
        self._master.triggerScopeManager.run_wave(dacarray, ttlarray, params)


    def setParams(self, analogLine, digitalLine, length, trigMode, delayDAC, delayTTL, reps):
        params = dict([])
        params["analogLine"] = analogLine
        params["digitalLine"] = digitalLine
        params["length"] = length
        params["trigMode"] = trigMode
        params["delayDAC"] = delayDAC
        params["delayTTL"] = delayTTL
        params["reps"] = reps
        return params

