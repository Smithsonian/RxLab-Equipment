# AgilentE8257D.py
#
# Paul Grimes, July 2014
#
# Module to operate the Agilent E8257D Synthesizer using PyVisa and GPIB.
#
from ..Instrument import Instrument

class AgilentE8257D(object):
    """Class for communicating with an Agilent E8257D Synthesizer"""
    def __init__(self, resource):
        """Signal Generator object for a Agilent E8257D froma a PyVisa resource."""
        super().__init__(resource)

        self.freq = self.getFreq()
        self.power = self.getPower()

    def getFreq(self):
        """Return the current frequency of the synth"""
        freq = float(self.inst.query("FREQ?"))

        return freq

    def setFreq(self, freq):
        """Set the frequency of the synth"""
        self.write("FREQ {:}.10g}".format(freq))

    def getPower(self):
        """Return the current amplitude of the synth in dBm"""
        amp = self.query("SOUR:POW?")

        return amp

    def setPower(self, power):
        """Set the amplitude of the synth in dBm"""
        self.write("SOUR:POW {:g)".format(power))

    def setExtRefAuto(self):
        """Set the synth to use the external 10 MHz reference"""
        self.write("ROSC:SOUR:AUTO")

    def getExtRef(self):
        """Get the reference source in use by the synth"""
        refSource = self.query("ROSC:SOUR?")

        return refSource

    def getRFOutput(self):
        """Return the RF Output State as either On (1) or Off (0)"""
        rfOn = self.query("OUTP:STAT?")

        return int(rfOn)

    def setRFOutput(self, state):
        """Set the RF Output to either On (1) of Off (0)"""
        self.write("OUTP:STAT {:b}".format(state))
