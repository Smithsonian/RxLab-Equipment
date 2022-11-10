from enum import IntEnum

from . import Instrument
import numpy as np

def dBdeg2complex(amp, phase):
    """Convert amplitude in dB and phase in degrees to cartesian complex number"""
    return np.power(10.0, amp/20) * np.exp(1j*np.deg2rad(phase))

def lindeg2complex(amp, phase):
    """Convert amplitude in volts and phase in degrees to cartesian complex number"""
    return amp * np.exp(1j*np.deg2rad(phase))

class SR844(Instrument.Instrument):
    '''Class for communicating with an Stanford Research 844 RF Lock-in as a Vector Voltmeter'''
    
    outputs = IntEnum('outputs', ['X', 'Y', 'R', 'dBm', 'Theta'])
    inttime = {0:1e-4, 1:3e-4, 2:1e-3, 3:3e-3, 4:1e-2, 5:3e-2, 6:1e-1, 7:3e-1, 8:1., 9:3., 10:10., 11:30., 12:100., 13:300., 14:1.e3, 15:3.e3, 16:1.e4, 17:3.e4}
    
    def __init__(self, resource):
        """Create Vector Voltmeter object from PyVisa resource.

        rm = pyvisa.ResourceManager()
        pm = SR844(rm.open_resource(<InstAddr>))
        InstAddr is the PyVisa address of the VVM - try "GPIB0::8::INSTR" by default"""

        super().__init__(resource)

        # Set some internal state parameters to allow return values to be interpreted
        self.mode = "UNKNOWN"
        self._format = "POLAR"
        self._scale = "LOGARITHMIC"
        self._output = [outputs.dBm, outputs.Theta]
        self.format = self.getFormat()
        self.average = self.getAveraging()
        
        # Set termination characters
        self.resource.read_termination = '\n'
        self.resource.write_termination = '\n'
        
        # send output responses to GPIB
        self.write("OUTX 1")

    def setTransmission(self):
        '''Set the VVM to output transmission data - relative amplitude (A/B) and phase (A-B)'''
        #self.write("SENSE TRANSMISSION")
        self.mode = "TRANSMISSION"

    def setMode(self, mode):
        '''Set the VVM measurement mode

        mode can be any of:
        AVOLtage, BVOLtage - A and B voltages
        APOWer, BPOWer - A and B powers
        PHASe - phase between A and B
        TRANSMISSION - power and phase difference between A and B
        GDELay - Group delay between A and B
        SWR -
        RHO -
        Y
        Z
        CORE
        modes can be concatenated with comma separation'''
        self.write("SENSE {:s}".format(mode))
        self.mode = mode

    def setFormat(self, format):
        '''Set the output format of the VVM
        Valid options are:
            LIN - (Volts)
            LOG - (dB)
            POL - (amp in dB or volts, phase in deg)
            RECT - volts as (real, imag)
            CART - volts as (real, imag)
            '''
        self._format = format
        if "LOG" in format:
            self._scale = "LOGARITHMIC"
        elif "LIN" in format:
            self._scale = "LINEAR"
        
        if "POL" in format:
            self._format = "POLAR"
        elif "RECT" in format or "CART" in format:
            self._format = "RECTANGULAR"
            self._scale = "LINEAR"

    def getFormat(self):
        '''Return the current output format of the VVM'''
        return f"{self._scale},{self._format}"

    def setFormatLog(self):
        '''Set the output format of the VVM to LOG - (dB) or (dB, deg) for TRANSMISSION'''
        self.setFormat("LOG")

    def setWait(self, window):
        '''Set the multiple of the integration time to wait before reading'''
        self.averaging = window

    def getAveraging(self):
        '''Get the number of samples averaged for each data point'''
        return self.averaging

    def getWait(self):
        int_time = int(self.query("OFLT?"))
        
        return self.averaging * self.inttime[int_time]

    def getTransmission(self):
        '''Return the data from the VVM'''
        # Get the data
        datastr = self.query(f"SNAP? {self._output[0]},{self._output[1]}")
        
        if self.format == "POLAR":
            amp = float(datastr.split(",")[0])
            phase = float(datastr.split(",")[1])
                
            if self.scale == "LOGARITHMIC":
                data = dBdeg2complex(amp, phase)
            else:
                data = lindeg2complex(amp, phase)

        elif self.format == "RECTANGULAR":
            x = float(datastr.split(",")[0])
            y = float(datastr.split(",")[1])
            data = complex(x, y)

        return data

    def getUnits(self):
        ''' Returns units for format types'''
        if self.scale == "LINEAR":
            x_units = "volts"
        elif self.scale == "LOGARITHMIC":
            x_units = "dBm"

        if self.format == "POLAR":
            y_units = "deg"
        elif self.format == "RECTANGULAR":
            y_units = "Real + Imag"

        units = (x_units, y_units)

        return units
    
    def getPowers(self):
        '''For compatibility with code for HP8508As.'''
        return (1, np.abs(self.getTransmission()))

    def trigger(self):
        '''For compatibility with code for HP8508As.'''
        pass