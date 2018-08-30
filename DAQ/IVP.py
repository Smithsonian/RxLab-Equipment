##################################################
#                                                #
# IV testing with Power Meter                                     #
#                                                #
# Larry Gardner, July 2018                       #
# Paul Grimes, August 2018                       #
##################################################

import sys
import os
import time
import visa
import numpy as np
import DAQ
import matplotlib.pyplot as plt
import PowerMeter as PM
import gpib


class IVP:
    def __init__(self, use="IV.use", verbose=False):
        self.verbose = verbose

        self.pm = None
        self.reverseSweep = True
        self.settleTime = 0.1
        self._bias = 0.0
        self.use = use

        self.save_name = "iv.dat"
        self.vmin = 0.0
        self.vmax = 5.0
        self.step = 0.05

        if self.vmin > self.vmax:
            self.vmin, self.vmax = self.vmax, self.vmin
        self.readFile()
        self.initDAQ()
        self.initPM()

    def __delete__(self):
        self.endDAQ()
        self.endPM()

    def readFile(self):
        # Opens use file and assigns corresponding parameters
        if self.verbose:
            print("\nUSE file: ",self.use)
        f = open(self.use, 'r')
        lines = f.readlines()
        f.close()

        self.Vs_min = float(lines[0].split()[0])
        self.Vs_max = float(lines[1].split()[0])
        self.MaxDAC = float(lines[2].split()[0])
        self.Rate = int(lines[3].split()[0])
        self.Navg = int(lines[4].split()[0])
        self.G_v = float(lines[5].split()[0])
        self.G_i = float(lines[6].split()[0])
        self.Boardnum = int(lines[7].split()[0])
        self.Out_channel = int(lines[8].split()[0])
        self.V_channel = int(lines[9].split()[0])
        self.I_channel = int(lines[10].split()[0])
        # Bias range is +/- 15mV, DAQ output range is 0-5V. Voltage offset is required for Volt < 0.
        self.V_offset = float(lines[11].split()[0])
        self.pm_address = lines[12].split()[0]

    def voltOut(self, bias):
        """Converts bias voltage to output voltage from DAQ"""
        return bias * self.G_v / 1000 + self.V_offset

    def biasIn(self, volt):
        """Converts input voltage to bias voltage at device"""
        return (volt - self.V_offset) * 1000 / self.G_v

    def currIn(self, volt):
        """Converts input voltage from current channel to bias current at device"""
        return (volt - self.V_offset) / self.G_i

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

    def initDAQ(self):
        # Lists available DAQ devices and connects the selected board
        self.daq = DAQ.DAQ()
        self.daq.listDevices()
        self.daq.connect(self.Boardnum)

    def initPM(self, pm_address=None):
        # Initializes Power Meter
        if pm_address==None:
            pm_address = self.pm_address

        try:
            rm = visa.ResourceManager("@py")
            lr = rm.list_resources()
            if pm_address in lr:
                self.pm = PM.PowerMeter(rm.open_resource(pm_address))
                self.pm_address = pm_address
                if self.verbose:
                    print("Power Meter connected.\n")
            else:
                self.pm = None
                if self.verbose:
                    print("No Power Meter detected.\n")
        except gpib.GpibError:
            self.pm = None
            if self.verbose:
                print("GPIB Error connecting to Power Meter.\n")
        except:
            self.pm = None
            if self.verbose:
                print("Unknown Error connecting to Power Meter.\n")

    def bias(self, bias):
        """Short cut to set the bias point to <bias> mV and return the
        resulting bias point"""
        self.setBias(bias)
        data = self.getData()

        if self.verbose:
            print("New Bias Point:")
            if len(data) == 3:
                print("  Voltage: {:f} mV, Current: {:f} mA, IF Power: {:f} W".format(data[0], data[1], data[2]))
            else:
                print("  Voltage: {:f} mV, Current: {:f} mA".format(data[0], data[1]))
        return data

    def setBias(self, bias):
        """Sets the bias point to request value in mV"""
        # Converts desired bias amount [mV] to DAQ output voltage value [V]
        self._bias = bias
        self.setVoltOut(self.voltOut(self._bias))

    def getData(self):
        """Gets V, I and P (if PM present) data, and returns it as a tuple"""
        # Sets proper format for low and high channels to scan over
        channels = [self.V_channel, self.I_channel]
        low_channel, high_channel = min(channels), max(channels)
        data = self.daq.AInScan(low_channel, high_channel, self.Rate, self.Navg)
        if self.pm != None:
            Pdata = self.pm.getData(rate="I")
        # Get the output voltage/curret data
        Vdata = self.calcV(data[self.V_channel])
        Idata = self.calcI(data[self.I_channel])

        if self.pm != None:
            return Vdata, Idata, Pdata
        else:
            return Vdata, Idata

    def calcV(self, volts):
        """Converts ADC reading in volts to bias voltage in mV"""
        return (volts - self.V_offset) * 1000 / self.G_v

    def calcI(self, volts):
        """Converts ADC reading in volts to bias current in uA"""
        return (volts - self.V_offset) / self.G_i

    def setVoltOut(self, volt):
        """Sets the DAC output voltage and waits to settle"""
        # Sets bias to specified voltage
        self.daq.AOut(volt, self.Out_channel)
        time.sleep(self.settleTime)

    def sweep(self):
        """Short cut to prep, run and end sweep"""
        self.prepSweep()
        self.runSweep()
        self.endSweep()


    def prepSweep(self):
        # Sanity check values to make sure that requested bias range is
        # within bias limits
        self.crop()

        print("Preparing for sweep...")
        # Calculate sweep values
        self.BiasPts = np.arange(self.vmin, self.vmax+self.step, self.step)
        if self.reverseSweep:
            self.BiasPts = np.flipud(self.BiasPts)

        # Prepares for data collection
        self.Vdata = np.empty_like(self.BiasPts)
        self.Idata = np.empty_like(self.BiasPts)
        self.Pdata = np.empty_like(self.BiasPts)

        # Setting voltage to max in preparation for sweep
        if self.reverseSweep:
            if self.verbose:
                print("\nChanging voltage to maximum...")
        else:
            if self.verbose:
                print("\nChanging voltage to minimum...")

        self.setVoltOut(self.voltOut(self.BiasPts[0]))


    def runSweep(self):
        if self.verbose:
            print("\nRunning sweep...")

        # Sets proper format for low and high channels to scan over
        channels = [self.V_channel, self.I_channel]
        low_channel, high_channel = min(channels), max(channels)

        if self.verbose:
            print("\tBias (mV)\tVoltage (mV)\tCurrent (mA)\tIF Power")

        for index, bias in enumerate(self.BiasPts):
            self.setVoltOut(self.voltOut(bias))

            #Collects data from scan
            data = self.getData()

            self.Vdata[index] = data[0]
            self.Idata[index] = data[1]
            if self.pm != None:
                self.Pdata[index] = data[2]
            else:
                self.Pdata[index] = 0.0

            if index%5 == 0 and self.verbose:
                print("\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t{:.3g}".format(self.BiasPts[index], self.Vdata[index], self.Idata[index], self.Pdata[index]))


    def endSweep(self):
        # Sets bias to zero to end sweep.
        self.setBias(self._bias)
        if self.verbose:
            print("Sweep is over.  Bias reset to {:.3f} mV.".format(self._bias))


    def endDAQ(self):
        # Disconnects and releases selected board number
        self.daq.disconnect(self.Boardnum)


    def endPM(self):
        # Disconnects power meter
        if self.pm != None:
            self.pm.close()

    def spreadsheet(self):
        if self.verbose:
            print("\nWriting data to spreadsheet...")

        # Creates document for libre office
        out = open(str(self.save_name) + ".xlsx", 'w')

        # Writes data to spreadsheet
        if self.pm != None:
            out.write("Voltage (mV) \tCurrent (mA) \tPower (W)\n")
            for i in range(len(self.Vdata)):
                out.write(str(self.Vdata[i]) + "\t" + str(self.Idata[i]) + "\t" + str(self.Pdata[i]) + "\n")
        else:
            out.write("Voltage (mV) \tCurrent (mA) \n")
            for i in range(len(self.Vdata)):
                out.write(str(self.Vdata[i]) + "\t" + str(self.Idata[i]) + "\n")

        out.close()

    def plotIV(self):
        # Plot IV curve
        plt.plot(self.Vdata,self.Idata, 'ro-')
        plt.xlabel("Voltage (mV)")
        plt.ylabel("Current (mA)")
        plt.title("IV Sweep - 15mV")
        plt.axis([min(self.Vdata), max(self.Vdata), min(self.Idata), max(self.Idata)])
        plt.show()

    def plotPV(self):
        # Plot PV curve
        if self.pm != None:
            plt.plot(self.Vdata, self.Pdata, 'bo-' )
            plt.xlabel("Voltage (mV)")
            plt.ylabel("Power (W)")
            plt.title("PV - 15mV")
            plt.axis([min(self.Vdata), max(self.Vdata), min(self.Pdata), max(self.Pdata)])
            plt.show()


if __name__ == "__main__":
    # This code runs a sweep from <vmax> to <vmin> with stepsize <step> and
    # saves the data to <save_name>
    #
    # Usage: python3 <file.dat> <vmin> <vmax> <step> <*use file>

    test = IVP(verbose=True)

    if len(sys.argv) >= 5:
        test.save_name = sys.argv[1]
        test.vmin = float(sys.argv[2])
        test.vmax = float(sys.argv[3])
        test.step = float(sys.argv[4])
        if len(sys.argv) == 6:
            test.use = sys.argv[5]
    else:
        test.save_name = input("Output file name: ")
        test.vmin = float(input("Minimum voltage [mV]: "))
        test.vmax = float(input("Maximum voltage [mV]: "))
        test.step = float(input("Step [mV]: "))
        if test.step <= 0:
            while test.step <= 0:
                print("Step size must be greater than 0.")
                test.step = float(input("Step [mV]: "))

    # Set up the IV object
    test.readFile()
    test.initDAQ()
    test.initPM()

    # Run a sweep
    test.sweep()

    # Output and plot data
    test.spreadsheet()
    test.plotIV()
    test.plotPV()

    # Close down the IV object cleanly, releasing the DAQ and PM
    del test

    print("\nEnd.")
