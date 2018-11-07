##################################################
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
import os
import time
import hjsonConfig
import jsonmerge
import numpy as np
import drivers.DAQ.DAQ as DAQ
import matplotlib.pyplot as plt

import _IV_default_config


class IV:
    def __init__(self, config=None, configFile="IV_config.hjson", verbose=False):
        """Create an IV object that can set a bias via the DAQ, read bias voltages
        and currents, and run a sweep over bias points."""
        self.verbose = verbose

        self.pm = None
        self.reverseSweep = True
        self.settleTime = 0.01
        self._bias = 0.0

        # Load the default config
        self.config = _default_IV_config.config

        self.save_name = "iv.dat"
        self.vmin = 0.0
        self.vmax = 5.0
        self.step = 0.05

        if self.vmin > self.vmax:
            self.vmin, self.vmax = self.vmax, self.vmin

        self.daq = DAQ.DAQ(autoConnect=False)

        if configFile != None:
            self.config = !!!!hjsonConfig.read(configFile)
        if config != None:
            self.setConfig(config)
        self.initDAQ()

    def __delete__(self):
        """Run this before deleting the IV object, to release the DAQ board"""
        self.endDAQ()


    def processConfig(self):
        """Process the configuration"""
        # Try and parse any daq elements in the config file
        try:
            self.daq.setConfig(config=self.config["daq"])
        except KeyError:
            pass

        self.vOut_channel = self.config["vOut"]["channel"]
        self.vOut_gain = self.config["vOut"]["gain"]
        self.vOut_offset = self.config["vOut"]["offset"]

        self.vIn_channel = self.config["vIn"]["channel"]
        self.vIn_gain = self.config["vIn"]["gain"]
        self.vIn_offset = self.config["vIn"]["offset"]

        self.iIn_channel = self.config["iIn"]["channel"]
        self.iIn_gain = self.config["iIn"]["gain"]
        self.iIn_offset = self.config["iIn"]["offset"]

        self.Vs_min = self.config["Vmin"]
        self.Vs_max = self.config["Vmax"]
        self.Rate = self.config["rate"]
        self.Navg = self.config["average"]

    def crop(self):
        # Limits set voltages to max and min sweep voltages
        if self.vmin < self.Vs_min:
            self.vmin = self.Vs_min
        if self.vmin > self.Vs_max:
            self.vmin = self.Vs_max
        if self.vmax < self.Vs_min:
            self.vmax = self.Vs_min
        if self.vmax > self.Vs_max:
            self.vmax = self.Vs_max

    def sort(self):
        """Make sure that vmax is greater than vmin"""
        if self.vmin > self.vmax:
            v = self.vmin
            self.vmin = self.vmax
            self.vmax = v
            self.reverseSweep = not self.reverseSweep
        if self.step < 0:
            self.step = -self.step
            self.reverseSweep = not self.reverseSweep


    def initDAQ(self):
        """Lists available DAQ devices, connects the selected board and sets the AI Range"""

        self.daq.setAiRangeValue(self.AiRange)


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
        if volt > self.MaxDAC:
            if self.verbose:
                print("DAC Maximum output voltage of {:.2f} exceeded - clipping to max".format(self.MaxDAC))
            volt = self.MaxDAC
        if volt < 0.0:
            if self.verbose:
                print("DAC Minimum output voltage of 0.00 V exceeded - clipping to min")
            volt = 0.0

        # Sets bias to specified voltage
        self.daq.AOut(volt, channel=self.Out_channel)
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
        self.crop()
        self.sort()

        print("Preparing for sweep...")
        # Calculate sweep values
        self.BiasPts = np.arange(self.vmin, self.vmax+self.step, self.step)
        if self.reverseSweep:
            if self.verbose:
                print("Flipping BiasPts")
            self.BiasPts = np.flipud(self.BiasPts)

        # Prepares for data collection
        self.Vdata = np.empty_like(self.BiasPts)
        self.Idata = np.empty_like(self.BiasPts)

        # Setting voltage to max in preparation for sweep
        if self.reverseSweep:
            if self.verbose:
                print("\nChanging voltage to maximum...")
        else:
            if self.verbose:
                print("\nChanging voltage to minimum...")

        self._oldBias = self._bias
        self.setBias(self.BiasPts[0])


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
            print("\tBias (mV)\tVoltage (mV)\tCurrent (mA)")

        # Carry out the sweep
        for index, bias in enumerate(self.BiasPts):
            self.setBias(bias)

            # Collects data from new bias point
            data = self.getData()

            self.Vdata[index] = data[0]
            self.Idata[index] = data[1]

            # Outputs data while sweep is being taken
            if index%5 == 0 and self.verbose:
                print("\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(bias, self.Vdata[index], self.Idata[index]))


    def endSweep(self):
        """Sets bias to initial value to end sweep.

        This should be overidden when subclassing IV.py to create a new sweep
        type"""
        self.setBias(self._oldBias)
        if self.verbose:
            print("Sweep is over.  Bias reset to {:.3f} mV.".format(self._bias))


    def endDAQ(self):
        """Disconnects and releases selected board number"""
        self.daq.disconnect(self.Boardnum)


    def spreadsheet(self):
        """Output the acquired data to a CSV file.

        This should be overridden to output additional data when subclassing IV
        """
        if self.verbose:
            print("\nWriting data to spreadsheet...")

        out = open(self.save_name, 'w')

        # Write a header describing the data
        out.write("# Bias (mV)\t\tVoltage (mV)\t\tCurrent (mA)\n")
        # Write out the data
        for i in range(len(self.Vdata)):
            out.write("{:.6g},\t{:.6g},\t{:.6g}\n".format(self.BiasPts[i], self.Vdata[i], self.Idata[i]))
        out.close()

    def plotIV(self):
        """Plot the IV curve data on the figure"""
        self.ax.plot(self.Vdata, self.Idata, 'r-')
        self.ax.set(xlabel="Voltage (mV)")
        self.ax.set(ylabel="Current (mA)")
        self.ax.set(title="IV Sweep")
        self.ax.grid()
        #self.ax.axis([min(self.Vdata), max(self.Vdata), min(self.Idata), max(self.Idata)])

    def plot(self, ion=True):
        """Plot the acquired data from the sweep.

        This should be overridden to plot additional data when subclassing IV
        """
        if ion:
            plt.ion()
        self.fig, self.ax = plt.subplots()
        self.plotIV()
        self.fig.show()



if __name__ == "__main__":
    # This code runs a sweep from <vmax> to <vmin> with stepsize <step> and
    # saves the data to <save_name>
    #
    # Usage: python3 <file.dat> <vmin> <vmax> <step> <*use file>

    test = IV(verbose=True)

    if len(sys.argv) >= 5:
        test.save_name = sys.argv[1]
        test.vmin = float(sys.argv[2])
        test.vmax = float(sys.argv[3])
        test.step = float(sys.argv[4])
        if len(sys.argv) == 6:
            test.use = sys.argv[5]
            test.readFile()
            test.initDAQ()
    else:
        test.save_name = input("Output file name: ")
        test.vmin = float(input("Minimum voltage [mV]: "))
        test.vmax = float(input("Maximum voltage [mV]: "))

        test.step = float(input("Step [mV]: "))

    # Run a sweep
    test.sweep()

    # Output and plot data
    test.spreadsheet()
    plt.ion()
    test.plot()
    # Wait until the plot is done
    try:
        input("Press [enter] to continue.")
    except SyntaxError:
        pass


    # Close down the IV object cleanly, releasing the DAQ
    del test

    print("End.")
