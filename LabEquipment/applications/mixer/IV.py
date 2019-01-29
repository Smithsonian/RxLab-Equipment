#! /usr/bin/env python
#                                                #
# IV testing                                     #
#                                                #
# Larry Gardner, July 2018                       #
# Paul Grimes, August 2018                       #
# Edited Aug 2018 to remove power meter code.    #
# Aim is to have simple IV code that can be      #
# subclassed to produce more complex sweep       #
# code                                           #
##################################################

from __future__ import print_function, division

import sys
import time
import pprint
from pkg_resources import resource_filename

import numpy as np
import LabEquipment.drivers.DAQ.DAQ as DAQ
import matplotlib.pyplot as plt

from LabEquipment.lib import hjsonConfig

from LabEquipment.applications.mixer import _default_IV_config


class IV:
    def __init__(self, config=None, configFile=None, verbose=False, vverbose=False):
        """Create an IV object that can set a bias via the DAQ, read bias voltages
        and currents, and run a sweep over bias points."""
        self.verbose = verbose or vverbose
        self.vverbose = vverbose

        self.daq = DAQ.DAQ(autoConnect=False, verbose=self.vverbose)

        self.config = None
        self.setConfig(_default_IV_config.defaultConfig)

        self.fig = None

        if self.vverbose:
            print("IV.__init__: Default Config Loaded: Current config:")
            pprint.pprint(self.config)

        if configFile != None:
            self.readConfig(configFile)
            if self.vverbose:
                print("IV.__init__: Config Loaded from: {:s}".format(configFile))
                pprint.pprint(self.config)
        if config != None:
            if self.vverbose:
                print("IV.__init__: Config passed to __init__:")
                pprint.pprint(config)

            self.setConfig(config)

            if self.vverbose:
                print("IV.__init__: Config now:")
                pprint.pprint(self.config)


        if self.vverbose:
            print("IV.__init__: Done setting configFile and config: Current config:")
            pprint.pprint(self.config)

        self._bias = 0.0
        self.columnHeaders = "Bias (mV)\t\tVoltage (mV)\t\tCurrent (mA)"

        self.initDAQ()

    def readConfig(self, filename):
        """Read the .hjson configuration file to set up the DAQ unit."""
        # Opens use file
        self.configFile = filename

        if self.verbose:
            print("IV.readConfig: Reading config file: ", self.configFile)
        newConfig = hjsonConfig.hjsonConfig(filename=filename, verbose=self.vverbose)
        if self.vverbose:
            print("IV.readConfig: Read config: ")
            pprint.pprint(newConfig)
        self.setConfig(newConfig)


    def setConfig(self, config):
        """Merge a new config into the existing config.

        Called automatically from readFile()"""
        if self.vverbose:
            print("IV.setConfig: Merging New config:")
            pprint.pprint(config)
        self.config = hjsonConfig.merge(self.config, config)
        if self.vverbose:
            print("IV.setConfig: Merged Config:")
            pprint.pprint(self.config)
        self._applyConfig()


    def _applyConfig(self):
        """Apply the configuration to set up the object variables.  Will get
        called automatically from setConfig

        This should be overridden to read any additional configuration values
        when subclassing IV.py"""
        try:
            self.daq.setConfig(self.config["daq"])
        except KeyError:
            pass

        try:
            self.vOut_channel = self.config["vOut"]["channel"]
            self.vOut_gain = self.config["vOut"]["gain"]
            self.vOut_offset = self.config["vOut"]["offset"]
            self.Vs_min = self.config["vOut"]["Vsmin"]
            self.Vs_max = self.config["vOut"]["Vsmax"]


            self.vIn_channel = self.config["vIn"]["channel"]
            self.vIn_gain = self.config["vIn"]["gain"]
            self.vIn_offset = self.config["vIn"]["offset"]

            self.iIn_channel = self.config["iIn"]["channel"]
            self.iIn_gain = self.config["iIn"]["gain"]
            self.iIn_offset = self.config["iIn"]["offset"]

            self.Rate = self.config["rate"]
            self.Navg = self.config["average"]
            self.settleTime = self.config["settleTime"]

            self.sweepmin = self.config["sweep"]["min"]
            self.sweepmax = self.config["sweep"]["max"]
            self.step = self.config["sweep"]["step"]
            self.reverseSweep = self.config["sweep"]["reverse"]
            self.save_name = self.config["sweep"]["save-file"]
        except KeyError:
            if self.verbose:
                print("Got KeyError while applying IV config")
                pprint.pprint(self.config)
            raise

    def __delete__(self):
        """Run this before deleting the IV object, to release the DAQ board"""
        self.endDAQ()

    def initDAQ(self):
        """Connect the DAQ device"""
        self.daq.connect()
        self.daq.setAiRangeValue(self.daq.AiRange)

    def endDAQ(self):
        """Disconnects and releases the DAQ device"""
        self.daq.disconnect()


    def cropSweep(self):
        """Limits sweep voltages to max and min output voltages"""
        limVmin = self.Vs_min
        limVmax = self.Vs_max
        if self.sweepmin < limVmin:
            if self.verbose:
                print("Sweep min {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limVmin))
            self.sweepmin = limVmin
        if self.sweepmin > limVmax:
            if self.verbose:
                print("Sweep min {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limVmax))
            self.sweepmin = limVmax
        if self.sweepmax < limVmin:
            if self.verbose:
                print("Sweep max {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limVmin))
            self.sweepmax = limVmin
        if self.sweepmax > limVmax:
            if self.verbose:
                print("Sweep max {:f} exceeds limits, limiting to {:f}".format(self.sweepmax, limVmax))
            self.sweepmax = limVmax

    def sort(self):
        """Make sure that vmax is greater than vmin"""
        if self.sweepmin > self.sweepmax:
            v = self.sweepmin
            self.sweepmin = self.sweepmax
            self.sweepmax = v
            self.reverseSweep = not self.reverseSweep
        if self.step < 0:
            self.step = -self.step
            self.reverseSweep = not self.reverseSweep

    def bias(self, bias):
        """Short cut to set the bias point to <bias> mV and return the
        resulting bias point

        This should be overidden when subclassing IV.py to get any additional
        data required"""
        self.setBias(bias)
        data = self.getData()

        if self.verbose:
            print("New Bias Point: {:.4g} mV".format(bias))
            print("  Voltage: {:.4g} mV, Current: {:.4g} mA".format(data[0], data[1]))
        return data

    def setBias(self, bias):
        """Sets the bias point to request value in mV"""
        # Converts desired bias amount [mV] to DAQ output voltage value [V]
        self._bias = bias
        self.setVoltOut(self.calcBias(self._bias))

    def setVoltOut(self, volt):
        """Sets the DAC output voltage and waits to settle"""
        if volt > self.daq.AoRange.range_max:
            if self.verbose:
                print("Requested output of {:.2f} exceeds DAC maximum output voltage of {:.2f} - clipping to max".format(volt, self.daq.AoRange.range_max))
            volt = self.daq.AoRange.range_max
        if volt < self.daq.AoRange.range_min:
            if self.verbose:
                print("Requested output of {:.2f} exceeds DAC minimum output voltage of {:.2f} - clipping to max".format(volt, self.daq.AoRange.range_min))
            volt = self.daq.AoRange.range_min

        # Sets bias to specified voltage
        self.daq.AOut(volt, channel=self.vOut_channel)
        time.sleep(self.settleTime)

    def getData(self):
        """Gets V and I data, and returns it as a tuple

        This should be overidden when subclassing IV.py to to get any additional
        data required"""

        data = self.getRawData()

        # Get the output voltage/current data
        Vdata = self.calcV(data[self.vIn_channel])
        Idata = self.calcI(data[self.iIn_channel])

        return Vdata, Idata

    def getRawData(self):
        """Gets the voltages from the DAQ"""
        # Sets proper format for low and high channels to scan over
        channels = [self.vIn_channel, self.iIn_channel]
        low_channel, high_channel = min(channels), max(channels)
        data = self.daq.AInScan(low_channel, high_channel, self.Rate, self.Navg)
        return np.mean(data[:, self.vIn_channel]), np.mean(data[:, self.iIn_channel])

    def calcBias(self, bias):
        """Converts bias voltage to output voltage from DAQ"""
        return bias * self.vOut_gain + self.vOut_offset

    def calcBiasOut(self, biasVout):
        """Converts output voltage from DAQ to mixer bias"""
        return (biasVout - self.vOut_offset) / self.vOut_gain

    def calcV(self, volts):
        """Converts ADC reading in volts to bias voltage in mV"""
        return (volts - self.vIn_offset) * 1000 / self.vIn_gain

    def calcI(self, volts):
        """Converts ADC reading in volts to bias current in mA"""
        return (volts - self.iIn_offset) / self.iIn_gain

    def sweep(self):
        """Short cut to prep, run and end the sweep"""
        self.prepSweep()
        self.runSweep()
        self.endSweep()


    def prepSweep(self):
        """Prepare to run a sweep.

        Sets up the points to sweep over, initializes storage for acquired data
        and sets the bias point to the initial point.

        This should be overidden when subclassing IV.py to create a new sweep
        type"""
        # Sanity check values to make sure that requested bias range is
        # within bias limits and that vmin, vmax and step values are sane
        self.cropSweep()
        self.sort()

        print("Preparing for sweep...")
        # Calculate sweep values
        self.SweepPts = np.arange(self.sweepmin, self.sweepmax+self.step, self.step)
        if self.reverseSweep:
            if self.verbose:
                print("Flipping SweepPts")
            self.SweepPts = np.flipud(self.SweepPts)

        # Prepares for data collection
        self.Vdata = np.empty_like(self.SweepPts)
        self.Idata = np.empty_like(self.SweepPts)

        # Setting voltage to max in preparation for sweep
        if self.reverseSweep:
            if self.verbose:
                print("\nChanging voltage to maximum...")
        else:
            if self.verbose:
                print("\nChanging voltage to minimum...")

        self._oldBias = self._bias
        self.setSweep(self.SweepPts[0])


    def runSweep(self):
        """Runs the sweep.

        This should be overidden when subclassing IV.py to create a new sweep
        type"""
        if self.verbose:
            print("\nRunning sweep...")

        # Sets proper format for low and high channels to scan over
        channels = [self.vIn_channel, self.iIn_channel]
        low_channel, high_channel = min(channels), max(channels)

        # Print a header for intermediate output
        if self.verbose:
            print("\t{:s}\n".format(self.columnHeaders))

        # Carry out the sweep
        for index, sweepPt in enumerate(self.SweepPts):
            self.setSweep(sweepPt)

            # Collects data from new bias point
            data = self.getData()

            self.Vdata[index] = data[0]
            self.Idata[index] = data[1]

            # Outputs data while sweep is being taken
            if index%5 == 0 and self.verbose:
                print("\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(self.SweepPts[index], self.Vdata[index], self.Idata[index]))

    def setSweep(self, sweepPt):
        """Set the bias to the sweepPt value.

        When subclassing, set this to whatever method is required to set the sweep variable."""
        self.setBias(sweepPt)


    def endSweep(self):
        """Sets bias to initial value to end sweep.

        This should be overidden when subclassing IV.py to create a new sweep
        type"""
        self.setBias(self._oldBias)
        if self.verbose:
            print("Sweep is over.  Bias reset to {:.3f} mV.".format(self._bias))


    def spreadsheet(self):
        """Output the acquired data to a CSV file.

        This should be overridden to output additional data when subclassing IV
        """
        if self.verbose:
            print("\nWriting data to spreadsheet...")

        out = open(self.save_name, 'w')

        # Write a header describing the data
        out.write("# {:s}\n".format(self.columnHeaders))
        # Write out the data
        for i in range(len(self.Vdata)):
            out.write("{:.6g},\t{:.6g},\t{:.6g}\n".format(self.SweepPts[i], self.Vdata[i], self.Idata[i]))
        out.close()

    def plotIV(self):
        """Plot the IV curve data on the figure"""
        self.ax.plot(self.Vdata, self.Idata, 'k-')
        self.ax.set(xlabel="Voltage (mV)")
        self.ax.set(ylabel="Current (mA)")
        self.ax.set(title="IV Sweep")
        self.ax.grid()
        #self.ax.axis([min(self.Vdata), max(self.Vdata), min(self.Idata), max(self.Idata)])

    def plot(self, ion=True):
        """Plot the acquired data from the sweep.

        This should be overridden to plot additional data when subclassing IV
        """
        #if ion:
        #    plt.ion()
        self.fig, self.ax = plt.subplots()
        self.plotIV()
        plt.show()

    def savefig(self, filename=None):
        """Save the current figure to a file"""
        if filename==None:
            filename = self.save_name.split(".")[:-1]
            filename.append("png")
            filename = ".".join(filename)

        if self.fig:
            self.fig.savefig(filename)


if __name__ == "__main__":
    # This code runs a sweep from <max> to <min> with stepsize <step> and
    # saves the data to <save_name>
    #
    # Usage: python3 <file.dat> <min> <max> <step> <*use file>

    test = IV(verbose=True, vverbose=True)

    if len(sys.argv) >= 5:
        if len(sys.argv) == 6:
            test.readFile(sys.argv[5])
            test.initDAQ()
        test.save_name = sys.argv[1]
        test.sweepmin = float(sys.argv[2])
        test.sweepmax = float(sys.argv[3])
        test.step = float(sys.argv[4])

    else:
        test.save_name = input("Output file name: ")
        test.sweepmin = float(input("Minimum voltage [mV]: "))
        test.sweepmax = float(input("Maximum voltage [mV]: "))

        test.step = float(input("Step [mV]: "))

    # Run a sweep
    test.sweep()

    # Output and plot data
    test.spreadsheet()
    #plt.ion()
    test.plot()
    # Wait until the plot is done
    try:
        input("Press [enter] to continue.")
    except SyntaxError:
        pass


    # Close down the IV object cleanly, releasing the DAQ
    del test

    print("End.")
