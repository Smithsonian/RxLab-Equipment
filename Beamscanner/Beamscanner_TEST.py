#############################################################
# Beam scanner test: 1 MSL and no HMCT2240 signal generator #
#                                                           #
# Larry Gardner, July 2018                                  #
#############################################################

import visa
import os
import time
import pyoo
import sys

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
import numpy.polynomial.polynomial as poly
from time import sleep

import HP8508A
import HMCT2240
import MSL
        
        
class Beamscanner:
    def __init__(self):

        # Instruments
        self.vvm = None
        self.msl_x = None
        self.msl_y = None
        self.sg = None
    
    def initTime(self):
        # Assigns start time
        self.start_time = time.time()
    
    def readUSE(self):
        # If use file is entered, use that file instead of default.
        if len(sys.argv) > 1:
            useFile = sys.argv[1]
        else:
            useFile = "Beamscan.use"
        print("USE file: ",useFile)
        
        # Reads USE file for parameters
        f = open(useFile, 'r')
        lines = f.readlines()
        f.close()
        self.save_name = lines[0].split()[0]
        self.Range = float(lines[1].split()[0])
        self.Step = float(lines[2].split()[0])
        self.Average = int(lines[3].split()[0])
        self.Format = lines[4].split()[0]
        self.Freq = float(lines[5].split()[0])
        self.conv_factor = int(lines[6].split()[0])
    
    def initGPIB(self):
        # Configures GPIB upon new bus entry
        os.system("sudo gpib_config")
        # Lists available resources
        rm = visa.ResourceManager('@py')
        lr = rm.list_resources()
        print("GPIB devices configured. \nAvailable Resources: "+str(lr))
        return rm
    
    def initVVM(self):
        # Initializes voltmeter parameters
        self.vvm.setTransmission()
        self.vvm.setFormat(self.Format)
        self.vvm.setAveraging(self.Average)
        self.vvm.setTriggerBus()
        print("\nVVM format: " + str(bs.vvm.getFormat()) + "\n")
        
    def initSG(self):
        # Initializes signal generator parameters
        self.sg.setFreq(self.Freq)
        self.sg.on()
        print("Signal generator is ON at frequency of " + str(freq) + ".")
        
    def initMSL(self):
        # Initializes MSL home positions to minimum travel position to synchronize between tests
        self.msl_x.zero()
        #self.msl_y.zero()
        self.msl_x.hold()
        #self.msl_y.hold()
        
    def setRange(self, Range):
        # Range of travel stage motion (50x50mm)
        self.pos_x_max = int((Range/2) * self.conv_factor) # 25 mm * 5000 microsteps per mm
        #self.pos_y_max = self.pos_x_max
        self.pos_x_min = -self.pos_x_max
        #self.pos_y_min = self.pos_x_min
        self.pos_y_max = int(Range/2)
        self.pos_y_min = -int(Range/2)

    def setStep(self, res):
        # Sets step size for position increments
        # Converts resolution in mm to microsteps for MSL
        step = int(res * self.conv_factor)
        return step
    
    def findMaxPos(self):
        # Finds the X and Y positions of maximum voltmeter amplitude
        # Function only used in "findCenter"
        max_amp = max(self.vvm_data, key = lambda x: x[0])
        index = self.vvm_data.index(max_amp)
        self.pos_x_center = int(self.pos_data[index][0])
        self.pos_y_center = int(self.pos_data[index][1])

    def findCenter(self):
        # Runs scan over area & finds maximum amplitude peak.
        # Begins at arbitrary position and decreases range and resolution with each iteration
        
        print("Finding center...")
        
        res = 2.5
        Range = 10
        self.pos_x_center = int(50 * self.conv_factor)
        self.pos_y_center = int(50 * self.conv_factor)
        
        while res >= .1:
            self.moveToCenter()
            self.initScan(Range)
            self.scan(res)
            self.findMaxPos()
            
            Range = res * 2
            res = res / 5
        
        print("\n")
        
    def moveToCenter(self):
        # Moves MSL's to center position and sets new home position
        self.msl_x.moveAbs(self.pos_x_center)
        #self.msl_y.moveAbs(self.pos_y_center)
        self.msl_x.hold()
        #self.msl_y.hold()
        self.msl_x.setHome()
        #self.msl_y.setHome()
       
    def initScan(self, Range):
        self.setRange(Range)
        # Moves to minimum position in range to begin scan
        self.msl_x.moveAbs(self.pos_x_min)
        #self.msl_y.moveAbs(self.pos_y_min)
        self.msl_x.hold()
        #self.msl_y.hold()
        
        # Gets initial position
        self.pos_x = int(self.msl_x.getPos())
        #self.pos_y = int(self.msl_y.getPos())
        self.pos_y = int(self.pos_y_min)

        # VVM ready to begin collecting data
        self.vvm.trigger()
    
    def scan(self, res):
        step = self.setStep(res)
        # Establish data arrays and parameters
        self.vvm_data = []
        self.pos_data = []
        self.time_data = []

        self.direction = "right"
        self.delay = 0
        
        while self.pos_y <= self.pos_y_max:
            # "Direction" is the direction at which the X MSL travels
            # "Direction" gets reversed to maximize speed
            if self.direction == "right":
                while self.pos_x <= self.pos_x_max:
                    # Collects VVM and position data
                    time.sleep(self.delay)
                    self.time_data.append(time.time())
                    trans = self.vvm.getTransmission()
                    self.vvm_data.append(trans)
                    self.pos_data.append((self.pos_x/self.conv_factor,self.pos_y))
                    print("    X: " + str(self.pos_x/self.conv_factor) + ", Y: " + str(self.pos_y))
                    print("    " + str(trans))
                    # X MSL steps relatively, if not in maximum position
                    if self.pos_x != self.pos_x_max:
                        self.msl_x.moveRel(step)
                        self.msl_x.hold()
                        self.pos_x = int(self.msl_x.getPos())
                    elif self.pos_x == self.pos_x_max:
                        break
            
                self.direction = "left"
                pass
    
            elif self.direction == "left":
                while self.pos_x >= self.pos_x_min:
                    # Collects VVM and position data
                    time.sleep(self.delay)
                    self.time_data.append(time.time())
                    trans = self.vvm.getTransmission()
                    self.vvm_data.append(trans)
                    self.pos_data.append((self.pos_x/self.conv_factor,self.pos_y))
                    print("    X: " + str(self.pos_x/self.conv_factor) + ", Y: " + str(self.pos_y))
                    print("    " + str(trans))
                    # X MSL steps relatively in opposite direction (-), if not in minimum position
                    if self.pos_x != self.pos_x_min:
                        self.msl_x.moveRel(-step)
                        self.msl_x.hold()
                        self.pos_x = int(self.msl_x.getPos())
                    elif self.pos_x == self.pos_x_min:
                        break
                    
                self.direction = "right"
                pass
            
            # Y MSL steps relatively. Use Y step increment if testing using only 1 MSL
            '''
            self.msl_y.moveRel(step)
            self.msl_y.hold()
            self.pos_y = int(self.msl_y.getPos())
            '''
            self.pos_y += step / self.conv_factor
            
        time_initial = self.time_data[0]
        for i in range(len(self.time_data)):
            self.time_data[i] = self.time_data[i] - time_initial
            
    def endSG(self):
        # Turns off signal generator output
        self.sg.off()
    
    def spreadsheet(self):
        print("Writing data to spreadsheet...")
        
        # Creates localhost for libre office
        os.system("soffice --accept='socket,host=localhost,port=2002;urp;' --norestore --nologo --nodefault # --headless")

        # Uses pyoo to open spreadsheet
        desktop = pyoo.Desktop('localhost',2002)
        doc = desktop.create_spreadsheet()
    
        x_data = []
        y_data = []
        amp_data = []
        phase_data = []
    
        for i in range(len(self.pos_data)):
            x_data.append(self.pos_data[i][0])
            y_data.append(self.pos_data[i][1])

            # Reformats VVM data if not already in proper form
            if type(self.vvm_data[i]) == tuple:
                amp_data.append(self.vvm_data[i][0])
                phase_data.append(self.vvm_data[i][1])
            elif type(vvm_data[i]) == str:
                amp_data.append(float(self.vvm_data[i].split(",")[0]))
                phase_data.append(float(self.vvm_data[i].split(",")[1]))
    
        try:
            # Writes data to spreadsheet
            sheet = doc.sheets[0]
            sheet[0,0:5].values = ["Time (s)","X Position (mm)", "Y Position (mm)", "Amplitude (dB)", "Phase (deg)"]
            sheet[1:len(self.time_data)+1, 0].values = self.time_data
            sheet[1:len(self.pos_data)+1, 1].values = x_data
            sheet[1:len(self.pos_data)+1, 2].values = y_data
            sheet[1:len(self.pos_data)+1, 3].values = amp_data
            sheet[1:len(self.pos_data)+1, 4].values = phase_data
    
            doc.save('BeamScannerData/' + str(self.save_name) + '.xlsx')
            doc.close()
    
        except (ValueError, KeyboardInterrupt, RuntimeError):
            doc.close()
            pass
            
            
    def contour_plot(self):
        # Makes contour plot given beamscanner object data format, not spreadsheet data format
        x_data = []
        y_data = []
        amp_data = []    

        for i in range(len(self.pos_data)):
            x_data.append(self.pos_data[i][0])
            y_data.append(self.pos_data[i][1])
    
            if type(self.vvm_data[i]) == tuple:
                amp_data.append(self.vvm_data[i][0])
        
            elif type(self.vvm_data[i]) == str:
                amp_data.append(float(self.vvm_data[i].split(",")[0]))
    
        pos_x_min = min(x_data)
        pos_x_max = max(x_data)
        pos_y_min = min(y_data)
        pos_y_max = max(y_data)
        
        xi = np.linspace(pos_x_min, pos_x_max, 1000)
        yi = np.linspace(pos_y_min, pos_y_max, 1000)
        zi = griddata(x_data, y_data, amp_data, xi, yi, interp = "linear")

        CS = plt.contour(xi, yi, zi, levels=[-35,-30,-25,-20, -15, -10, -5], colors='black')
        plt.clabel(CS, inline =1)
        plt.xlabel("X Position (mm)")
        plt.ylabel("Y Position (mm)")
        matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
        plt.xlim(pos_x_min, pos_x_max)
        plt.ylim(pos_y_min, pos_y_max)
        plt.title("Amplitude vs. Position")
        plt.show()
    
    def time_plot(self):
        # Makes time vs amplitude & phase plot given beamscanner data format, not spreadsheet data format
        amp_data = []
        phase_data = []

        for i in self.vvm_data:
            if type(self.vvm_data[i]) == tuple:
                amp_data.append(i[0])
                phase_data.append(i[1])
        
            elif type(self.vvm_data[i]) == str:
                amp_data.append(float(i.split(",")[0]))
                phase_data.append(float(i.split(",")[1]))
        
        fig, ax1 = plt.subplots()
    
        ax1.plot(self.time_data, amp_data, 'bD--', label = "Amplitude (dB)")
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude (dB)', color='b')
        ax1.tick_params('y', colors='b')
        plt.legend(loc = "upper left")
    
        ax2 = ax1.twinx()
        ax2.plot(self.time_data, phase_data, 'r^-', label = "Phase (deg)")
        ax2.set_ylabel('Phase (deg)', color='r')
        ax2.tick_params('y', colors='r')
        plt.legend(loc = "upper right")
        
        fig.tight_layout()
        plt.show()
    
    def y_plot(self):
        # Makes plot of amplitude & phase vs. Y-position along X = 0 plane
        y_data = []
        amp_data = []
        phase_data = []    

        for i in range(len(self.pos_data)):
            if self.pos_data[i][0] == 0:
                y_data.append(self.pos_data[i][1])
    
                if type(self.vvm_data[0]) == tuple:
                    amp_data.append(self.vvm_data[i][0])
                    phase_data.append(self.vvm_data[i][1])
        
                elif type(self.vvm_data[0]) == str:
                    amp_data.append(float(self.vvm_data[i].split(",")[0]))
                    phase_data.append(float(self.vvm_data[i].split(",")[1]))
            
        fig, ax1 = plt.subplots()
    
        x_new = np.linspace(y_data[0], y_data[-1], num=len(y_data)*10)
    
        coefs_amp = poly.polyfit(y_data, amp_data, 2)    
        fit_amp = poly.polyval(x_new, coefs_amp)
        ax1.plot(y_data, amp_data, 'bD', label = "Amp (meas)")
        ax1.plot(x_new, fit_amp, 'b--', label = "Amp (fitted)")
        ax1.set_xlabel("Y position (mm)")
        ax1.set_ylabel("Amplitude (dB)", color='b')
        ax1.tick_params('y', colors='b')
        ax1.legend(loc = "upper left")
        
        coefs_phase = poly.polyfit(y_data, phase_data, 2)
        fit_phase = poly.polyval(x_new, coefs_phase)
        ax2 = ax1.twinx()
        ax2.plot(y_data, phase_data, 'r^', label = "Phase (meas)")
        ax2.plot(x_new, fit_phase, 'r-', label = "Phase (fitted)")
        ax2.set_ylabel('Phase (deg)', color='r')
        ax2.tick_params('y', colors='r')
        ax2.legend(loc = "upper right")
        
        fig.tight_layout()
        plt.show()
    


if __name__ == "__main__":

    # Begin
    bs = Beamscanner()
    print("\nStarting...\n")
    bs.initTime()
    bs.readUSE()

    # Establishes instrument communication
    rm = bs.initGPIB()   
    bs.vvm = HP8508A.HP8508A(rm.open_resource("GPIB0::8::INSTR"))
    bs.msl_x = MSL.MSL(rm.open_resource("ASRL/dev/ttyUSB0"))
    #bs.msl_y = MSL.MSL(rm.open_resource("ASRL/dev/ttyUSB1"))
    
    # Initializes instruments
    bs.initVVM()
    bs.initMSL()

    # Find center of beam to calibrate to
    bs.findCenter()
    
    # Preparing to scan
    print("\nPreparing for data ...")
    bs.moveToCenter()
    bs.initScan(bs.Range)

    # Scanning    
    print("\nCollecting data ...")
    bs.scan(bs.Step)

    # Finished scanning
    print("\nExecution time: " + str(time.time() - bs.start_time))
    
    # Writing to spread sheet
    bs.spreadsheet()
    '''
    print("Plotting data ...")
    # Plots position vs. amplitude contour plot via function
    bs.contour_plot()
    # Plots amplitude and phase vs. time
    bs.time_plot()
    # Plots amplitude and phase vs. y position for slice at center of beam
    bs.y_plot()
    '''
    print("\nEnd.")

    
