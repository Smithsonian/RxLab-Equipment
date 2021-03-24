#! /usr/bin/env python
##################################################
#                                                #
# IV testing with IF power from power meter or   #
# ADC                                            #
#                                                #
# Larry Gardner, July 2018                       #
# Paul Grimes, November 2018                     #
##################################################

from __future__ import print_function, division

import sys
import time
import visa
import numpy as np
import pprint

import matplotlib.pyplot as plt
import LabEquipment.drivers.Instrument.HP436A as PM

from LabEquipment.applications.mixer import _default_IVP_timestream_config
from LabEquipment.applications.mixer import IVP


class IVP_timestream(IVP.IVP):
    """An object that can measure the bias on an SIS device, and measure
    the IF power an analog power signal connected to the bias DAQ unit over
    time"""
    def __init__(self, config=None, configFile=None, verbose=False, vverbose=False):
        super().__init__(config=config, configFile=configFile, verbose=verbose, vverbose=vverbose)
        self.setConfig(_default_IVP_timestream_config.defaultConfig)

        if self.vverbose:
            print("IVP_timestream.__init__: Default Config Loaded: Current config:")
            pprint.pprint(self.config)

        if configFile != None:
            self.readConfig(configFile)
            if self.vverbose:
                print("IVP_timestream.__init__: Config Loaded from: {:s}".format(configFile))
                pprint.pprint(self.config)
        if config != None:
            if self.vverbose:
                print("IVP_timestream.__init__: Config passed to __init__:")
                pprint.pprint(config)

            self.setConfig(config)

            if self.vverbose:
                print("IVP_timestream.__init__: Config now:")
                pprint.pprint(self.config)

        if self.vverbose:
            print("IVP_timestream.__init__: Done setting configFile and config: Current config:")
            pprint.pprint(self.config)

        self.columnHeaders = "Time (s)\tVoltage (mV)\tCurrent (mA)\tIF Power"
        self.pm = None

        self.initPM()

    def __delete__(self):
        self.endPM()
        super().__delete__()

    def _applyConfig(self):
        super()._applyConfig()
        try:
            self.sampleTime = self.config["timestream"]["sampleTime"]
            self.streamLength = self.config["timestream"]["streamLength"]
        except KeyError:
            self.sampleTime = 0.01
            self.streamLength = 100

    def prepSweep(self):
        self.SweepPts = np.arange(0, self.streamLength, 1)

        # Prepares for data collection
        self.Vdata = np.empty_like(self.SweepPts, dtype=np.float)
        self.Idata = np.empty_like(self.Vdata)
        self.Pdata = np.empty_like(self.Vdata)
        self.Tdata = np.empty_like(self.Vdata)


    def runSweep(self):
        if self.verbose:
            print("\nRunning sweep...")

        if self.verbose:
            print("\t{:s}\n".format(self.columnHeaders))

        time0 = time.time()

        for index, bias in enumerate(self.SweepPts):
            #self.setSweep(bias)

            #Collects data from scan
            t = time.time() - time0
            data = self.getData()

            self.Tdata[index] = t
            self.Vdata[index] = data[0]
            self.Idata[index] = data[1]
            if len(data) >= 3:
                self.Pdata[index] = data[2]
            else:
                self.Pdata[index] = 0.0

            if index%100 == 0 and self.verbose:
                print("\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t{:.3g}".format(self.Tdata[index], self.Vdata[index], self.Idata[index], self.Pdata[index]))

    def endSweep(self):
        """Do nothing because we didn't do anyting"""
        pass

    def spreadsheet(self):
        if self.verbose:
            print("\nWriting data to spreadsheet...")

        # Creates document for libre office
        out = open(self.save_name, 'w')

        # Writes data to spreadsheet
        # Write a header describing the data
        out.write("# {:s}\n".format(self.columnHeaders))
        for i in range(len(self.Vdata)):
            out.write("{:.6g},\t{:.6g},\t{:.6g},\t{:.6g}\n".format(self.Tdata[i], self.Vdata[i], self.Idata[i], self.Pdata[i]))

        out.close()

    def plotIT(self):
        self.ax.plot(self.Tdata, self.Idata, 'r-', label="Current")
        self.ax.set(ylabel="Current")
        self.ax.set(title="Current/Power Timestream")

    def plotPT(self):
        # Plot PV curve
        self.ax2.plot(self.Tdata, self.Pdata, 'b-', label="IF Power")
        self.ax2.set(ylabel="IF Power")
        #self.ax2.set(title="Power Timestream")

    def plot(self, ion=True):
        """Plot the acquired data from the sweep.
        """
        self.fig, self.ax = plt.subplots()
        self.plotIT()
        self.ax2 = self.ax.twinx()
        self.plotPT()
        plt.legend()
        plt.show()

if __name__ == "__main__":
    # This code runs a sweep from <max> to <min> with stepsize <step> and
    # saves the data to <save_name>
    #
    # Usage: python3 <file.dat> <min> <max> <step> <*use file>

    if len(sys.argv) == 5 or len(sys.argv) == 2:
        confFile = sys.argv.pop(1)
    else:
        confFile = "IVP_timestream-config.hjson"

    test = IVP_timestream(configFile=confFile, verbose=True, vverbose=False)

    if len(sys.argv) >= 4:
        test.save_name = sys.argv[1]
        test.sampleTime = float(sys.argv[2])
        test.streamLength = int(sys.argv[3])
    else:
        try:
            sweepConf = test.config["sweep"]
        except KeyError:
            test.save_name = input("Output file name: ")
            test.sampleTime = float(input("Time between samples (s):"))
            test.streamLength = float(input("Number of samples: "))


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
