#! /usr/bin/env python
##################################################
#                                                #
# IF frequency sweeping with YIG filter and      #
# IF power from power meter or ADC               #
#                                                #
# Paul Grimes, January 2019                      #
##################################################

from __future__ import print_function, division

import sys
import time
import visa
import numpy as np
import pprint

import matplotlib.pyplot as plt
import LabEquipment.drivers.Instrument.MLBF as MLBF

# create this
from LabEquipment.applications.mixer import _default_IFP_config
from LabEquipment.applications.mixer import IVP


class IFP(IVP.IVP):
    """An object that can set the frequency of a YIG filter, and measure
    the IF power with either a GPIB connected power meter or an analog power
    signal connected to the bias DAQ unit"""
    def __init__(self, config=None, configFile=None, verbose=False, vverbose=False):
        super().__init__(config=config, configFile=configFile, verbose=verbose, vverbose=vverbose)
        self.setConfig(_default_IFP_config.defaultConfig)

        if self.vverbose:
            print("IFP.__init__: Default Config Loaded: Current config:")
            pprint.pprint(self.config)

        if configFile != None:
            self.readConfig(configFile)
            if self.vverbose:
                print("IFP.__init__: Config Loaded from: {:s}".format(configFile))
                pprint.pprint(self.config)
        if config != None:
            if self.vverbose:
                print("IFP.__init__: Config passed to __init__:")
                pprint.pprint(config)

            self.setConfig(config)

            if self.vverbose:
                print("IFP.__init__: Config now:")
                pprint.pprint(self.config)

        if self.vverbose:
            print("IFP.__init__: Done setting configFile and config: Current config:")
            pprint.pprint(self.config)

        self.yig = None
        self.columnHeaders = "YIG Freq (GHz)\tVoltage (mV)\tCurrent (mA)\tIF Power"

        self.initYIG()

    def __delete__(self):
        self.endYIG()
        super().__delete__()

    def _applyConfig(self):
        super()._applyConfig()
        try:
            self.yig_address = self.config["yig-filter"]["address"]
            if self.verbose:
                print("UDP YIG filter configuration found")
        except KeyError:
            try:
                self.yig_address = None
                self.yigOut_channel = self.config["yig-filter"]["channel"]
                self.yigOut_gain = self.config["yig-filter"]["gain"]
                self.yigOut_offset = self.config["yig-filter"]["offset"]
                if self.verbose:
                    print("Analog YIG filter output configuration found")
            except KeyError:
                if self.verbose:
                    print("No YIG filter configuration found")
            self.yig = None

    def initYIG(self, yig_address=None):
        # Initializes Power Meter
        if yig_address==None:
            yig_address = self.yig_address

        if yig_address==None:
            # We don't have configuration for GPIB power meter, so we will
            # assume an analog signal is connected to the DAQ ADC input
            if self.verbose:
                print("No UDP YIG filter configured, using DAC output {:d}".format(self.yigOut_channel))
            return

        if yig_address:
            try:
                self.yig = MLBF.MLBF(yig_address)
                if self.yig.ip_address:
                    print("YIG filter {:}:{:} connected on {:}.\n".format(self.yig.model, self.yig.serial, self.yig.ip_address))
            except:
                self.yig = None
                if self.verbose:
                    print("Error connecting to YIG filter on {:}.\n".format(yig_address))

    def endYIG(self):
        """Closes the YIG connection.

        No action required for MLBF over UDP"""
        self.yig = None

    def setYIGFreq(self, freq):
        """Set the YIG frequency to <freq> GHz"""
        if self.yig: # Using YIG driver class
            self.yig.f = freq*1000.0 # YIG driver class works in MHz
            time.sleep(self.settleTime)
        else: # Using DAC output
            self.setYIGVoltOut(self.calcYIGBias(freq))

    def calcYIGBias(self, freq):
        """Calculate the bias voltage required to set the YIG filter to requested frequency
        in GHz"""
        return freq * self.yigOut_gain + self.yigOut_offset

    def setYIGVoltOut(self, volt):
        """Sets the DAC output voltage for the YIG and waits to settle"""
        if volt > self.daq.AoRange.range_max:
            if self.verbose:
                print("Requested output of {:.2f} exceeds DAC maximum output voltage of {:.2f} - clipping to max".format(volt, self.daq.AoRange.range_max))
            volt = self.daq.AoRange.range_max
        if volt < self.daq.AoRange.range_min:
            if self.verbose:
                print("Requested output of {:.2f} exceeds DAC minimum output voltage of {:.2f} - clipping to max".format(volt, self.daq.AoRange.range_min))
            volt = self.daq.AoRange.range_min

        # Sets bias to specified voltage
        self.daq.AOut(volt, channel=self.yigOut_channel)
        time.sleep(self.settleTime)


    def cropSweep(self):
        """Limits sweep frequencies to max and min YIG frequencies

        Overrides cropSweep from IV object"""
        limFmin = self.yig.fmin/1000.0
        limFmax = self.yig.fmax/1000.0
        if self.sweepmin < limFmin:
            if self.verbose:
                print("Sweep min {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limFmin))
            self.sweepmin = limFmin
        if self.sweepmin > limFmax:
            if self.verbose:
                print("Sweep min {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limFmax))
            self.sweepmin = limFmax
        if self.sweepmax < limFmin:
            if self.verbose:
                print("Sweep max {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limFmin))
            self.sweepmax = limFmin
        if self.sweepmax > limFmax:
            if self.verbose:
                print("Sweep max {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limFmax))
            self.sweepmax = limFmax

    # reuse IVP.getData() etc.

    def prepSweep(self):
        """Store current YIG filter setting, then reuse IVP.prepSweep()"""
        self._oldYIGFreq = self.yig.f/1000.0
        super().prepSweep()

    # reuse IVP.runSweep()

    def setSweep(self, sweepPt):
        """Override IV setSweep to set YIG frequency instead of bias"""
        self.setYIGFreq(sweepPt)

    def endSweep(self):
        """Sets YIG frequency to initial value to end sweep.

        This should be overidden when subclassing IFP.py to create a new sweep
        type"""
        self.setYIGFreq(self._oldYIGFreq)
        if self.verbose:
            print("Sweep is over.  YIG filter reset to {:.3f} GHz.".format(self.yig.f/1000.0))

    def spreadsheet(self):
        if self.verbose:
            print("\nWriting data to spreadsheet...")

        # Creates document for libre office
        out = open(self.save_name, 'w')

        # Writes data to spreadsheet
        # Write a header describing the data
        out.write("# {:s}\n".format(self.columnHeaders))
        for i in range(len(self.Vdata)):
            out.write("{:.6g},\t{:.6g},\t{:.6g},\t{:.6g}\n".format(self.SweepPts[i], self.Vdata[i], self.Idata[i], self.Pdata[i]))

        out.close()

    def plotPF(self):
        # Plot PF curve
        self.ax2.plot(self.SweepPts, self.Pdata, 'b-')
        self.ax2.set(xlabel="YIG Frequency (GHz)")
        self.ax2.set(ylabel="IF Power")
        self.ax2.set(title="IF Sweep")

    def plot(self, ion=True):
        """Plot the acquired data from the sweep.
        """
        self.fig, self.ax2 = plt.subplots()
        self.plotPF()
        plt.show()

if __name__ == "__main__":
    # This code runs a sweep from <vmax> to <vmin> with stepsize <step> and
    # saves the data to <save_name>
    #
    # Usage: python3 <file.dat> <vmin> <vmax> <step> <*use file>

    test = IFP(verbose=True, vverbose=True)

    if len(sys.argv) >= 5:
        if len(sys.argv) == 6:
            test.readFile(sys.argv[5])
            test.initDAQ()
        test.save_name = sys.argv[1]
        test.vmin = float(sys.argv[2])
        test.vmax = float(sys.argv[3])
        test.step = float(sys.argv[4])
    else:
        test.save_name = input("Output file name: ")
        test.vmin = float(input("Minimum frequency [GHz]: "))
        test.vmax = float(input("Maximum frequency [GHz]: "))
        test.step = float(input("Step [GHz]: "))

    # Run a sweep
    test.sweep()

    # Output and plot data
    test.spreadsheet()
    test.plot()
    # Wait until the plot is done
    try:
        save = input("Save Plot? [Y/N]")
        if save =="Y":
            test.savefig()
    except SyntaxError:
        pass


    # Close down the IV object cleanly, releasing the DAQ and PM
    del test

    print("End.")
