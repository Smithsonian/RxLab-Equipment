##################################################
#                                                #
# IV testing                                     #
#                                                #
# Larry Gardner, July 2018                       #         
#                                                #
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


class IV:
    def __init__(self):        
        self.PM = None
        self.pm_is_connected = False
        self.reverseSweep = True
        self.settleTime = 0.1
        
        if len(sys.argv) >= 5:
            self.save_name = sys.argv[1]
            self.vmin = float(sys.argv[2])
            self.vmax = float(sys.argv[3])
            self.step = float(sys.argv[4])
            if len(sys.argv) == 6:
                self.use = sys.argv[5]
            else:
                self.use = "IV.use"
        else:
            self.save_name = input("Save name: ")
            self.vmin = float(input("Minimum voltage [mV]: "))
            self.vmax = float(input("Maximum voltage [mV]: "))
            self.step = float(input("Step [mV]: "))
            if self.step <= 0:
                while self.step <= 0:
                    print("Step size must be greater than 0.")
                    self.step = float(input("Step [mV]: "))
            self.use = "IV.use"
            
        self.Navg = 10000
        if self.vmin > self.vmax:
            self.vmin, self.vmax = self.vmax, self.vmin
     
    def readFile(self):
        # Opens use file and assigns corresponding parameters
        print("\nUSE file: ",self.use)
        f = open(self.use, 'r')
        lines = f.readlines()
        f.close()
        
        self.Vs_min = float(lines[0].split()[0])
        self.Vs_max = float(lines[1].split()[0])
        self.MaxDAC = float(lines[2].split()[0])
        self.Rate = int(lines[3].split()[0])
        self.G_v = float(lines[4].split()[0])
        self.G_i = float(lines[5].split()[0])
        self.Boardnum = int(lines[6].split()[0])
        self.Out_channel = int(lines[7].split()[0])
        self.V_channel = int(lines[8].split()[0])
        self.I_channel = int(lines[9].split()[0])
        # Bias range is +/- 15mV, DAQ output range is 0-5V. Voltage offset is required for Volt < 0. 
        self.V_offset = float(lines[10].split()[0])
    
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
    
    def initPM(self):
        # Initializes Power Meter
        try:
            rm = visa.ResourceManager("@py")
            lr = rm.list_resources()
            pm = 'GPIB0::12::INSTR'
            if pm in lr:
                self.pm = PM.PowerMeter(rm.open_resource("GPIB0::12::INSTR"))
                self.pm_is_connected = True
                print("Power meter connected.\n")
            else:
                self.pm_is_connected = False
                print("No power meter detected.\n")
        except gpib.GpibError:
            self.pm_is_connected = False
            print("No power meter detected.\n")
    
    def setBias(self, bias):
        """Sets the bias point to request value"""
        # Converts desired bias amount [mV] to DAQ output voltage value [V]
        self.bias = bias
        self.volt_out = self.voltOut(self.bias)
        
        self.setVoltOut(self.volt_out)
    
    def setVoltOut(self, volt):
        """Sets the DAC output voltage"""
        # Sets bias to specified voltage
        self.daq.AOut(volt, self.Out_channel)
        time.sleep(self.settleTime)
        
    
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
        self.Vdata_rawinput = np.empty_like(self.BiasPts)
        self.Idata_rawinput = np.empty_like(self.BiasPts)
        self.Vdata = np.empty_like(self.BiasPts)
        self.Idata = np.empty_like(self.BiasPts)
        self.Pdata = np.empty_like(self.BiasPts)
        # Setting voltage to max in preparation for sweep
        if self.reverseSweep:
            print("\nChanging voltage to maximum...")
        else:
            print("\nChanging voltage to minimum...")
        self.bias = self.BiasPts[0]
        self.setBias(self.bias)

        
    def runSweep(self):
        print("\nRunning sweep...")
    
        # Sets proper format for low and high channels to scan over
        channels = [self.V_channel, self.I_channel]
        low_channel, high_channel = min(channels), max(channels)
        
        for index, bias in enumerate(self.BiasPts):
            self.setBias(bias)
            
            #Collects data from scan
            data = self.daq.AInScan(low_channel, high_channel, self.Rate, self.Navg)
            
            # Appends input voltage data
            self.Vdata_rawinput[index] = data[self.V_channel]
            self.Idata_rawinput[index] = data[self.I_channel]
            
            if self.pm_is_connected == True:
                self.Pdata.append(self.pm.getData())
                
            # Reformat data (Converts DAQ input voltage to correct voltage and current)
            self.Vdata[index] = (self.Vdata_rawinput[index] - self.V_offset) * 1000 / self.G_v 
            self.Idata[index] = (self.Idata_rawinput[index] - self.V_offset) / self.G_i
            
            if index%5 == 0:
                print(str(round(self.Vdata[index],2)) + ' mV \t' + str(round(self.Idata[index],2)) + ' mA')
                print("BIAS: " + str(round(self.bias, 2)) + " mV")
                print("Output voltage: " + str(round(self.volt_out,2)) + " V") 
                
            
            
    def endSweep(self):
        # Sets bias to zero to end sweep.
        self.bias = 0
        self.setBias(self.bias)
        print("\nBias set to zero. \nSweep is over.")
       
    def endDAQ(self):
        # Disconnects and releases selected board number
        self.daq.disconnect(self.Boardnum)
        
    def endPM(self):
        # Disconnects power meter
        if self.pm_is_connected == True:
            self.pm.close()
    
    def spreadsheet(self):
        print("\nWriting data to spreadsheet...")
        
        # Creates document for libre office
        out = open(str(self.save_name) + ".xlsx", 'w')
    
        # Writes data to spreadsheet
        if self.pm_is_connected == True:
            out.write("Voltage (mV) \tCurrent (mA) \tPower (W)\n")
            for i in range(len(Vdata)):
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
        if self.pm_is_connected == True:
            plt.plot(self.Vdata, self.Pdata, 'bo-' )
            plt.xlabel("Voltage (mV)")
            plt.ylabel("Power (W)")
            plt.title("PV - 15mV")
            plt.axis([min(self.Vdata), max(self.Vdata), min(self.Pdata), max(self.Pdata)])
    
    
if __name__ == "__main__":
    test = IV()
    test.readFile()
    test.initDAQ()
    test.initPM()
    test.prepSweep()
    test.runSweep()
    test.endSweep()
    test.endDAQ()
    test.endPM()
    test.spreadsheet()
    test.plotIV()
    test.plotPV()
    
    print("\nEnd.")
    
