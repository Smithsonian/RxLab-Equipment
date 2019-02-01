# HP83630A.py
#
# Paul Grimes, July 2014
#
# Module to operate the HP 83630A Synthesizer using PyVisa and GPIB.
#
import visa

class HP83630A(object):
    """Class for communicating with an HP 83630A Synthesizer"""
    def __init__(self, resource, strict=False, idString="83630A"):
        """Create Synthesizer object.

        InstAddr is the PyVisa address of the Synthesizer - try "GPIB::19" by default in the lab"""

        super().__init__(resource, strict, idString)

    def getFreq(self):
        """Return the current frequency of the synth"""
        freq = float(self.query("FREQ?"))

        return freq

    def setFreq(self, freq):
        """Set the frequency of the synth"""
        self.query("FREQ {.10g}".format(freq))

    def getAmp(self):
        """Return the current amplitude of the synth in dBm"""
        amp = float(self.query("POW?"))

        return amp

    def setAmp(self, amp):
        """Set the amplitude of the synth in dBm"""
        self.query("POW {:g}".format(amp))

    def setExtRefAuto(self):
        """Set the synth to use the external 10 MHz reference"""
        # TODO: Replace with correct command
        #self.write("ROSC:SOUR:AUTO")
        pass

    def getExtRef(self):
        """Get the reference source in use by the synth"""
        # TODO: Replace with correct command
        #refSource = self.query("ROSC:SOUR?")
        #return refSource
        pass

    def getRFOutput(self):
        """Return the RF Output State as either On (1) or Off (0)"""
        # TODO: Replace with correct command
        #rfOn = self.query("OUTP:STAT?")
        #return int(rfOn)
        pass

    def setRFOutput(self, state):
        """Set the RF Output to either On (1) of Off (0)"""
        # TODO: Replace with correct command
        #self.write("OUTP:STAT {:b}".format(state))
        pass
