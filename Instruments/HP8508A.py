# HP83630A.py
#
# Paul Grimes, Nov 2015
#
# Module to operate the HP 8508A Vector Voltmeter using PyVisa and GPIB.
#
# v2 - Nov 2015 - updated to work with new PyVISA 1.8 API and model.  Changed inheritance
# model to encapsulation (inherit from object, add first three lines in __init__), and implement
# write, read, query and ask methods.
#
# Updated and _v2 removed - Feb 2018.  Updated to subclass Instrument to simplify coding.


import visa
import Instrument

class HP8508A(Instrument.Instrument):
    '''Class for communicating with an HP 8508A Vector Voltmeter
    
    This class is instantiated by passing a PyVISA resource created
    by the visa resource manager.  e.g.:
    
    import visa
    rm = visa.ResourceManager()
    vvm = HP8508A(rm.open_resource('GPIB::8'))'''
    
    def __init__(self, resource, strict=False, idString="8508A-050"):
        # Set up the specifics for communication with the resource so that *IDN? will work
        # when checking ID
        resource.read_termination = "\n"
        resource.write_termination = "\n"
        
        # Call the __init__ function from Instrument.Instrument
        super(HP8508A, self).__init__(resource, strict, idstring)
        
        # Set some internal state parameters to allow return values to be interpreted
        self.mode = "UNKNOWN"
        self.format = self.getFormat()
        self.average = self.getAveraging()
        self.triggersource = "UNKNOWN"
        self.triggered = False
        
        
    def setMode(self, mode):
        '''Set the VVM measurement mode'''
        self.write("SENSE %s")
        self.mode = mode
    
    def setTransmission(self):
        '''Set the VVM to output transmission data - relative amplitude (A/B) and phase (A-B)'''
        self.write("SENSE TRANSMISSION")
        self.mode = "TRANSMISSION"
        
    def setTrigger(self, trigger):
        '''Set the trigger for the VVM data acquisition
        
        Valid options for the trigger are:
            BUS  - Trigger from Bus clock
            FREE - Freerunning'''
        self.write("TRIG:SOUR %s" % trigger)
        self.triggersource = trigger
        
    def setTriggerBus(self):
        '''Set the trigger to the Bus clock'''
        self.setTrigger("BUS")
        
    def setTriggerFree(self):
        '''Set the trigger to free run'''
        self.setTrigger("FREE")
        
    def setFormat(self, format):
        '''Set the output format of the VVM
        
        Valid options are:
            LIN - (Volts)
            LOG - (dB)
            POL - (amp in dB or volts, phase in deg)
            RECT - volts as (real, imag)
            CART - volts as (real, imag)
            '''
        self.write("FORMAT %s" % format)
        self.getFormat()
        
    def getFormat(self):
        '''Return the current output format of the VVM'''
        self.format = self.ask("FORMAT?")
        
        return self.format
        
    def setFormatLog(self):
        '''Set the output format of the VVM to LOG - (dB) or (dB, deg) for TRANSMISSION'''
        self.setFormat("LOG")
        
    def setAveraging(self, window):
        '''Set the VVM to average <window> samples before returning data'''
        self.write("AVER:COUN %d" % window)
        self.getAveraging()
        
    def getAveraging(self):
        '''Get the number of samples averaged for each data point'''
        self.averaging = int(self.ask("AVER:COUN?"))
        
        return self.averaging
        
    def trigger(self):
        '''Trigger a measurement with the VVM'''
        self.write("*TRG")
        self.triggered = True
        
    def getData(self, meas):
        '''Return the requested measurement(s) from the VVM
        
        <meas> is one of:
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
        
        <meas> can be concatenated with comma seperation
        '''
        # Trigger the measurement if required
        if self.triggersource == "BUS" and self.triggered == False:
            self.trigger()
        
        # Get the data
        datastr = self.ask("MEAS? %s" % meas)
        
        # Reset the triggered state
        self.triggered = False
        
        return datastr
        
    def getTransmission(self):
        '''Return the data from the VVM'''
        # Get the data
        datastr = self.getData("TRANSMISSION")
        
        if self.format == "LOGARITHMIC,POLAR":
            amp = float(datastr.split(",")[0])
            phase = float(datastr.split(",")[1])
            
            data = (amp, phase)
        else: # Unknown format, probably single valued
            try: 
                # Try to convert unknown format to a float, if not return raw string
                data = float(datastr)
            except ValueError:
                data = datastr
        
        return data
