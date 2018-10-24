from __future__ import print_function, division

import Instrument
import time

class PowerMeter(Instrument.Instrument):

    def __init__(self, resource):
        """Create Spectrum Analyzer object from a PyVISA resource:
        rm = visa.ResourceManager('@py')
        pm = PowerMeter(rm.open_resource(InstAddr))
        InstAddr is the address of the spectrum analyzer - try "GPIB0::12::INSTR" by default"""
        self.resource = resource

        # Set up the connection.
        # HP 436A needs a null line ending on write
        self.resource.read_termination = "\r\n"
        self.resource.timeout = 5000

        self._ranges = list(" IJKLM")
        self._modes = { "A":"Watts", "B":"dB Relative", "C": "dB Ref", "D":"dBm"}
        self._statuses = {"P":"Data Valid", "Q":"Watts, Under Range", "R":"Over Range", "S":"dB, Under Range", "T":"Auto Zero Under Range, 1", "U":"Auto Zero Under Range, 2-5", "V":"Auto Zero Over Range"}


    def getDataStr(self, pmrange="9", mode="A", cal_factor="+", rate="T"):
        """Get data str from power meter using <pmrange> <mode> and <rate>"""
        # pmrange is one of :
        #   1-5 : Most to least sensitive
        #   9   : Auto
        #
        # Mode is one of:
        #   A : Watts
        #   B : dB Relative
        #   C : dB Ref (switch pressed)
        #   D : dBm
        #
        # Cal Factor is one of:
        #   + : Disable
        #   - : Enable (front-panel switch setting)
        #
        # Measurement Rate is one of:
        #   H : Hold
        #   T : Trigger with settling time
        #   I : Trigger immediately
        #   R : Free-run at maximum rate
        #   V : Free-run with settling timeout

        self.resource.write("{}{}{}{}".format(pmrange, mode, cal_factor, rate))
        datastr = self.resource.read_bytes(14).decode('ascii')
        # Do this to flush the buffer
        if rate == "R" or rate == "V":
            self.resource.read()
        return datastr

    def unpackDataStr(self, dataStr):
        """Unpack the data string, returning the value in whatever mode we're in"""
        self.status = self._statuses[dataStr[0]]
        # Status is one of:
        #   P - Measured value valid
        #   Q - Watts mode under Range
        #   R - Over Range
        #   S - Under pmrange dBm or dB (rel) mode
        #   T - Power Sensor Auto Zero Loop Enabled; Range 1
        #           Under Range: (normal for auto zeroing on Range 1)
        #   U - Power Sensor Auto Zero Loop Enabled; Range !=1
        #           Under Range: (normal for auto zeroing on Range 2-5)
        #   V - Power Sensor Auto Zero Loop Enabled; Over Range

        # Range is one of:
        #   I-M, Range 1-5
        #
        # Convert to numerical range
        self.pmrange = self._ranges.index(dataStr[1])


        self.mode = self._modes[dataStr[2]]
        # Mode is one of:
        #   A - Watts
        #   B - dB Relative
        #   C - dB Ref (switch pressed)
        #   D - dBm

        sign = dataStr[3]
        if sign == " ":
            s = 1
        elif sign == "-":
            s = -1
        else:
            raise ValueError("Got wrong sign character from Power Meter - {}".format(sign))

        value = s*float(dataStr[4:12])

        return value

    def getData(self, pmrange="9", mode="A", cal_factor="+", rate="T"):
        """Return the power as a float, and set the properties of the PowerMeter
        object to describe the status and what the measurement represents

        In Rate R or V, the system will read until the timeout, and then
        return the first value only.

        Range is one of :
          1-5 : Most to least sensitive
          9   : Auto

        Mode is one of:
          A : Watts
          B : dB Relative
          C : dB Ref (switch pressed)
          D : dBm

        Cal Factor is one of:
          + : Disable
          - : Enable (front-panel switch setting)

        Measurement Rate is one of:
          H : Hold
          T : Trigger with settling time
          I : Trigger immediately
          R : Free-run at maximum rate
          V : Free-run with settling timeout
        """
        dataStr = self.getDataStr(pmrange, mode, cal_factor, rate)
        data = self.unpackDataStr(dataStr)
        return data

if __name__ == "__main__":
    import visa
    rm = visa.ResourceManager('@py')
    res = rm.open_resource("GPIB0::13::INSTR")
    pm = PowerMeter(res)

    print("Power : {:g} {:s}".format(pm.getData(), pm.mode))
    print("Range : {:d}".format(pm.pmrange))
    print("Status: {:s}".format(pm.status))
