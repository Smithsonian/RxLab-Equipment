#! /usr/bin/env python
##################################################
#                                                #
# IV sweeper that measured IF power from power   #
# meter or ADC for each of two receiver loads,   #
# sweeping in blocks, and calculates Y and Trx   #
#                                                #
# Paul Grimes, January 2019                      #
##################################################


from __future__ import print_function, division

import sys
import time
import visa
import numpy as np

import matplotlib.pyplot as plt

from LabEquipment.applications.mixer import IVP
from LabEquipment.applications.mixer import _default_IVY_config
from LabEquipment.applications.mixer import TempSensor

class IVY(IVP.IVP):
        """An object that can set and measure the bias on an SIS device, and measure
        the IF power for each of two receiver loads."""
        def __init__(self, config=None, configFile=None, verbose=False, vverbose=False):
            super().__init__(config=config, configFile=configFile, verbose=verbose, vverbose=vverbose)
            self.setConfig(_default_IVY_config.defaultConfig)

            if self.vverbose:
                print("IVY.__init__: Default Config Loaded: Current config:")
                pprint.pprint(self.config)

            if configFile != None:
                self.readConfig(configFile)
                if self.vverbose:
                    print("IVY.__init__: Config Loaded from: {:s}".format(configFile))
                    pprint.pprint(self.config)
            if config != None:
                if self.vverbose:
                    print("IVY.__init__: Config passed to __init__:")
                    pprint.pprint(config)

                self.setConfig(config)

                if self.vverbose:
                    print("IVY.__init__: Config now:")
                    pprint.pprint(self.config)

            if self.vverbose:
                print("IVY.__init__: Done setting configFile and config: Current config:")
                pprint.pprint(self.config)

            self.columnHeaders = "Bias (mV)\tVoltage (mV)\tCurrent (mA)\tHot IF Power\tCold IF Power\tY Factor\tNoise Temp"

    def _applyConfig(self):
        super()._applyConfig()

        try:
            self.loadSwitching = self.config["yfactor"]["load-switching"]
            self.innerScanCycle = self.config["yfactor"]["load-cycle-length"]
            self.coldLoadTemp = self.config["yfactor"]["cold-load-temp"]
            if self.coldLoadTemp == "sensor":
                if self.verbose:
                    print("Cold load sensor configuration found")
                try:
                    self.coldLoadSensor = TempSensor.TempSensor(config=self.config["yfactor"]["cold-load-sensor"])
                except KeyError:
                    if self.verbose:
                        print("Missing cold load sensor configuration")
            self.hotLoadTemp = self.config["yfactor"]["hot-load-temp"]
            if self.hotLoadTemp == "sensor":
                if self.verbose:
                    print("Hot load sensor configuration found")
                try:
                    self.hotLoadSensor = TempSensor.TempSensor(config=self.config["yfactor"]["hot-load-sensor"])
                except KeyError:
                    if self.verbose:
                        print("Missing hot load sensor configuration")
            if self.loadSwitching == "load-mover":
                if self.verbose:
                    print("Load mover configuration found")
                try:
                    self.loadMover = LoadMover.LoadMover(config=self.config["yfactor"]["load-mover"])
                except KeyError:
                    if self.verbose:
                        print("Missing load mover configuration")
            else: # manual, run entire scan in one block
                if self.innerScanCycle > 0:
                    self.innerScanCycle = 0
        except KeyError:
            if self.verbose:
                print("Invalid Y Factor configuration found")

    def prepSweep(self):
        """Prepare to run a sweep.

        Sets up the points to sweep over, initializes storage for acquired data
        and sets the bias point to the initial point.

        This should be overidden when subclassing IV.py to create a new sweep
        type"""
        # Use the IVP.prepSweep and IV.prepSweep methods
        super().prepSweep()

        # Add storage for hot and cold load IF powers, Y factors and Trx
        self.Hdata = np.empty_like(self.SweepPts)
        self.Cdata = np.empty_like(self.SweepPts)
        self.Ydata = np.empty_like(self.SweepPts)
        self.Trxdata = np.empty_like(self.SweepPts)
        self.Thdata = np.empty_like(self.SweepPts)
        self.Tcdata = np.empty_like(self.SweepPts)


    def runSweep(self):
        """Run the sweep, looping over SweepPts.

        Calls innerSweep() to run the sweep over blocks of SweepPts"""
        if self.verbose:
            print("\nRunning sweep...")

        if self.verbose:
            print("\t{:s}\n".format(self.columnHeaders))

        hotLoad = 1
        coldLoad = 0
        i = 0
        if self.innerScanCycle < len(self.SweepPts) and self.innerScanCycle > 0:
            j = self.innerScanCycle
        else:
            j = len(self.SweepPts)

        cont = True
        # Start of outer loop
        while cont:
            # check to see if j is exactly at or beyond end of SweepPts
            if j >= len(self.SweepPts):
                j = len(self.SweepPts)
                cont = False
            sweepPts = self.SweepPts[i:j]

            # Get hot load data
            load = hotLoad
            self.prepInnerSweep(load)
            Vdata, Idata, Pdata = self.innerSweep(sweepPts)
            self.Vdata[i:j] = Vdata
            self.Idata[i:j] = Idata
            self.Hdata[i:j] = Pdata
            if self.hotLoadTemp == "sensor":
                self.Thdata[i:j] = self.hotLoadSensorTemp
            else:
                self.Thdata[i:j] = self.hotLoadTemp

            # Get cold load data
            load = coldLoad
            self.prepInnerSweep(load)
            Vdata, Idata, Pdata = self.innerSweep(sweepPts)
            self.Vdata[i:j] = (Vdata + self.Vdata[i:j])/2.0
            self.Idata[i:j] = (Idata + self.Idata[i:j])/2.0
            self.Cdata[i:j] = Pdata
            if self.coldLoadTemp == "sensor":
                self.Tcdata[i:j] = self.coldLoadSensorTemp
            else:
                self.Tcdata[i:j] = self.coldLoadTemp

            # Calculate Y and Trx, and output updates if verbose
            self.Ydata[i:j] = self.calcY(start=i, end=j)
            self.Trxdata[i:j] = self.calcTrx(start=i, end=j)

            if self.verbose:
                for index in range(i, j, 5):
                    print("\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(self.SweepPts[index], self.Vdata[index], self.Idata[index], self.Hdata[index], self.Cdata[index], self.Ydata[index], self.Trxdata[index]))
            # increment indices for outer loop
            i = i+self.innerScanCycle
            j = j+self.innerScanCycle
        # End of outer loop


    def prepInnerSweep(self, variable):
        """Set up for the inner sweep.

        For IVY, this calls setLoadPosition, to set whether the hot or cold load is
        in the beam.

        Override this for other sweep types."""
        self.setLoadPostion(variable)


    def innerSweep(self, sweepPts):
        """An inner loop called within the main sweep.

        For IVY, this returns V, I and P data over sweepPts.

        Override this for other sweep types."""
        Vdata = np.empty_like(sweepPts)
        Idata = np.empty_like(sweepPts)
        Pdata = np.empty_like(sweepPts)

        for index, bias in enumerate(sweepPts):
            self.setSweep(bias)

            #Collects data from scan
            data = self.getData()

            Vdata[index] = data[0]
            Idata[index] = data[1]
            if len(data) >= 3:
                Pdata[index] = data[2]
            else:
                Pdata[index] = 0.0

        return Vdata, Idata, Pdata

    def setLoadPosition(self, position):
        """Set the ambient/hot load position.

        For manual mode, this means asking the user (nicely) to
        put the load in the beam and then tell the program that this
        has been done.

        If hotLoadTemp is set to "sensor", this also records the temperature
        of the load in self.hotLoadSensorTemp.

        We will assume that position 1 is hot load
        and position 0 is cold load"""
        if self.loadSwitching == "load-mover":
            if position == 1:
                self.loadMover.loadIn()
                if self.hotLoadTemp == "sensor":
                    self.hotLoadSensorTemp = self.hotLoadSensor.getT()
            elif position == 0:
                self.loadMover.loadOut()
                if self.coldLoadTemp == "sensor":
                    self.coldLoadSensorTemp = self.coldLoadSensor.getT()
            else:
                print("Requested load position not recognized, ignoring.")
        else:
            # We need to ask the user to move the load
            if position == 1:
                try:
                    save = input("Place hot load in beam and then press any key to continue.")
                except SyntaxError:
                    pass
            elif position == 0:
                try:
                    save = input("Place hot load in beam and then press any key to continue.")
                except SyntaxError:
                    pass
            else:
                print("Requested load position not recognized, ignoring.")

    def calcY(self, start=0, end=-1):
        """Calculate the Y factor by dividing Hdata by Cdata

        Start and end indices are passed by the inner loop to allow for intermediate
        output during a scan."""
        return self.Hdata[start:end]/self.Cdata[start:end]

    def calcTrx(self, start=0, end=-1):
        """Calculate the Noise Temperature using Y factor and Hot and Cold load temperatures

        Start and end indices are passed by the inner loop to allow for intermediate
        output during a scan."""
        return (self.Thdata[start:end] - self.Yfact[start:end]*self.Tcdata[start:end])/(self.Yfact[start:end]-1)

    def spreadsheet(self):
        """Output the acquired data to a CSV file.

        This should be overridden to output additional data when subclassing IVY
        """
        if self.verbose:
            print("\nWriting data to spreadsheet...")

        out = open(self.save_name, 'w')

        # Write a header describing the data
        out.write("# {:s}\n".format(self.columnHeaders))
        # Write out the data
        for i in range(len(self.Vdata)):
            out.write("{:.6g},\t{:.6g},\t{:.6g},\t{:.6g},\t{:.6g},\t{:.6g},\t{:.6g},\t{:.6g},\t{:.6g}\n".format(self.SweepPts[i], self.Vdata[i], self.Idata[i], self.Hdata[i], self.Cdata[i], self.Ydata[i], self.Trxdata[i], self.Thdata[i], self.Tcdata[i]))
        out.close()

    def plotPV(self):
        # Plot PV curve
        self.ax2.plot(self.Vdata, self.Hdata, 'r-', label="Hot")
        self.ax2.plot(self.Vdata, self.Cdata, 'b-', label="Cold")
        self.ax2.set(ylabel="Power (W)")

    def plotYV(self):
        """Plot the IV curve data on the figure"""
        self.ax.plot(self.Vdata, self.Idata, 'g-', label="Y Factor")
        self.ax.set(xlabel="Voltage (mV)")
        self.ax.set(ylabel="Y Factor")
        self.ax.set(title="Y Factor Sweep")
        self.ax.set_ylim(bottom=0)
        self.ax.grid()

    def plotTV(self):
        # Plot PV curve
        self.ax2.plot(self.Vdata, self.Trxdata, 'r-', label="T_rx")
        self.ax2.set(ylabel="Noise Temperature (K)")
        # Set some sensible limit on Y range
        maxPlot = np.percentile(np.clip(self.Trxdata, 0, None), 10)*10
        self.ax2.set_ylim(bottom=0, top=maxPlot)

    def plot(self, ion=True):
        """Plot the acquired data from the sweep.

        This should be overridden to plot additional data when subclassing IV
        """
        #if ion:
        #    plt.ion()
        self.fig, self.ax = plt.subplots()
        self.plotIV()
        self.ax2 = self.ax.twinx()
        self.plotPV()
        plt.show()

    def plot2(self, ion=True):
        """Plot the acquired data from the sweep.

        This should be overridden to plot additional data when subclassing IV
        """
        self.fig2, self.ax = plt.subplots()
        self.plotYV()
        self.ax2 = self.ax.twinx()
        self.plotTV()
        plt.show()


    def savefig(self, filename=None):
        """Save the current figure to a file"""
        if filename==None:
            filename = self.save_name.split(".")[:-1]
            filename.append("png")
            filename = ".".join(filename)

        if self.fig:
            self.fig.savefig(filename)

        if self.fig2:
            filename = filename.split(".")[:-1] + "Trx"
            filename.append("png")
            filename = ".".join(filename)
            self.fig2.savefig(filename)

if __name__ == "__main__":
    # This code runs a sweep from <max> to <min> with stepsize <step> and
    # saves the data to <save_name>
    #
    # Usage: python3 <file.dat> <min> <max> <step> <*use file>

    test = IVY(verbose=True, vverbose=True)

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
