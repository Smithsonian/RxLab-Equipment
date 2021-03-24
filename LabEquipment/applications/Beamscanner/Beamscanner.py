#############################################################
# Beamscanner class and program                             #
#                                                           #
# Larry Gardner, July 2018                                  #
#############################################################

import pyvisa
import os
import time
import sys

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import numpy.polynomial.polynomial as poly

import LabEquipment.drivers.Instrument.HP8508A as HP8508A
import LabEquipment.drivers.Instrument.HP83630A as HP83630A
import LabEquipment.drivers.Instrument.HMCT2240 as HMCT2240
import LabEquipment.drivers.Instrument.MSL as MSL

plt.ion()
plt.show()

class Beamscanner:
    def __init__(self):            
        self._debug = False

        # Instruments
        self.vvm = None
        self.msl_x = None
        self.msl_y = None
        self.RF = None
        self.LO = None
        self.centerBeforeScan = True
        self.verbose = False
        self.plotCenter = True
        self.scan_type = "raster"

    def initTime(self):
        # Assigns start time
        self.start_time = time.time()
        print("Starting...\n")

    def readUSE(self, useFile=None):
        # If use file is entered, use that file instead of default.
        if useFile == None:
            useFile = "Beamscan.use"


        print("USE file: ",useFile)

        # Reads USE file for parameters
        f = open(useFile, 'r')
        lines = f.readlines()
        f.close()

        # We need to know this first
        self.conv_factor = float(lines[13].split("!")[0])

        self.save_name = lines[0].split("!")[0].strip()
        self.Range = float(lines[1].split("!")[0])*self.conv_factor
        self.Res = float(lines[2].split("!")[0])*self.conv_factor
        self.Average = int(lines[3].split("!")[0])
        self.CalInterval = int(lines[4].split("!")[0])
        self.Format = lines[5].split("!")[0].strip()
        self.Testfreq = float(lines[6].split("!")[0])*1.0e9
        self.IFfreq = float(lines[7].split("!")[0])*1.0e6
        self.RFharm = int(lines[8].split("!")[0])
        self.RFfinalHarm = int(lines[9].split("!")[0])
        self.LOharm = int(lines[10].split("!")[0])
        self.RFpow = float(lines[11].split("!")[0])
        self.LOpow = float(lines[12].split("!")[0])
        self.searchCenter = (float(lines[14].split("!")[0].split(",")[0])*self.conv_factor, float(lines[14].split("!")[0].split(",")[1])*self.conv_factor)
        self.searchRange = float(lines[15].split("!")[0])*self.conv_factor
        self.searchRes = float(lines[16].split("!")[0])*self.conv_factor
        self.searchMinRes = float(lines[17].split("!")[0])*self.conv_factor
        self.velocity = float(lines[18].split("!")[0])
        self.accel = float(lines[19].split("!")[0])
        self.pos_x_center = self.searchCenter[0]
        self.pos_y_center = self.searchCenter[1]

        self.setStep(self.Res)
        self.calcFreqs()

    def printUSE(self):
        """Print the values read from the USE file"""
        print("""Use file:
{:s}    ! Save name
{:f}    ! Range
{:f}    ! Resolution
{:d}    ! Averaging
{:d}    ! Cal interval
{:s}    ! Format
{:f}    ! Test frequency
{:f}    ! IF frequency
{:d}    ! RF harmonic
{:d}    ! RF final harmonic
{:d}    ! LO harmonic
{:f}    ! RF power
{:f}    ! LO power
{:f}    ! Conversion factor
{:f}, {:f}  ! Search center
{:f}    ! Search range
{:f}    ! Search resolution
{:f}    ! Search minimum resolution
{:f}    ! Velocity
{:f}    ! Acceleration
""".format(
        self.save_name,
        self.Range,
        self.Res,
        self.Average,
        self.CalInterval,
        self.Format,
        self.Testfreq,
        self.IFfreq,
        self.RFharm,
        self.RFfinalHarm,
        self.LOharm,
        self.RFpow,
        self.LOpow,
        self.conv_factor,
        self.searchCenter[0], self.searchCenter[1],
        self.searchRange,
        self.searchRes,
        self.searchMinRes,
        self.velocity,
        self.accel))

    def calcFreqs(self):
        """Calculate the frequencies for the RF and LO based on the harmonics
        and test frequency"""
        self.RFfreq = self.Testfreq / self.RFharm
        self.reffreq = self.Testfreq / self.RFfinalHarm
        self.multLOfreq = self.Testfreq + self.IFfreq
        self.LOfreq = self.multLOfreq / self.LOharm

        if self.verbose:
            print("""
        Calculated frequencies in system:
            RF Output Frequency : {:8.4f} GHz
            RF Harmonic         : {:3d}
            RF Input Frequency  : {:8.4f} GHz

            IF Frequency        : {:8.4f} MHz

            LO Output Frequency : {:8.4f} GHz
            LO Harmonic         : {:3d}
            LO Input Frequency  : {:8.4f} GHz

            Final RF Multiplier : {:3d}
            Ref Frequency       : {:8.4f} GHz
            Ref LO Frequency    : {:8.4f} GHz
            Ref IF Frequency    : {:8.4f} MHz
        """.format(self.Testfreq/1e9, self.RFharm, self.RFfreq/1e9, self.IFfreq/1e6, self.multLOfreq/1e9, self.LOharm, self.LOfreq/1e9, self.RFfinalHarm, self.reffreq/1e9, self.multLOfreq/self.RFfinalHarm/1e9, self.IFfreq/self.RFfinalHarm/1e6))

    def initGPIB(self, backend="@py"):
        """Initialize PyVisa and check it's working.

        "no langid" errors are likely a permissions issue - make sure the current user
        has access to usb port and that linux-gpib is configured with gpib-config --minor=0.

        This can be done automatically at boot with udev rules

        see http://askubuntu.com/questions/705409/udev-rule-to-run-gpib-config and
        https://github.com/pyvisa/pyvisa/issues/212
        """
        # Lists available resources
        rm = pyvisa.ResourceManager(backend)
        try:
            lr = rm.list_resources()
        except ValueError:
            print("pyvisa list_resources failed - likely you have a permissions issue.  See Beamscanner.py Beamscanner.initGPIB() source for solutions")
        print("GPIB devices configured. \nAvailable Resources: "+str(lr))
        return rm

    def initVVM(self, format = "LOG,POLAR"):
        # Initializes voltmeter parameters
        self.vvm.setTransmission()
        self.vvm.setFormat(self.Format)
        self.vvm.setAveraging(self.Average)
        self.vvm.setTriggerBus()
        print("\nVVM format: {}".format(str(self.vvm.getFormat())))

    def initSG(self):
        # Initializes signal generator paramters
        self.RF.setFreq(self.RFfreq)
        self.RF.setPower(self.RFpow)
        self.RF.on()
        self.LO.setFreq(self.LOfreq)
        self.LO.setPower(self.LOpow)
        self.LO.on()
        print("RF: Frequency = {:f} Hz, Power = {:f} dBm".format(self.RFfreq, self.RFpow))
        print("LO: Frequency = {:f} Hz, Power = {:f} dBm".format(self.LOfreq, self.LOpow))

    def initMSL(self):
        if self.centerBeforeScan:
            # Sets MSL home positions to central position to synchronize between tests
            self.msl_x.center()
            self.msl_y.center()

        # Sets MSL motion parameters
        self.msl_x.setAccel(self.accel)
        self.msl_x.setDecel(self.accel)
        self.msl_x.setVelMax(self.velocity)
        self.msl_y.setAccel(self.accel)
        self.msl_y.setDecel(self.accel)
        self.msl_y.setVelMax(self.velocity)


    def setRangeMM(self, Range):
        """Sets the range to Range mm.
        Converts to MSL steps before calling .setRange()"""
        self.Range(Range*self.conv_factor)

    def setRange(self, Range):
        """Sets the range to Range steps"""
        self.pos_x_max = int(Range/2.0) + self.pos_x_center
        self.pos_y_max = int(Range/2.0) + self.pos_y_center
        self.pos_x_min = -int(Range/2.0) + self.pos_x_center
        self.pos_y_min = -int(Range/2.0) + self.pos_y_center

    def setStep(self, res):
        """Sets step size for position increments in MSL steps"""
        self.Step = res


    def setStepMM(self, res):
        """Sets step size for position increments
        Converts resolution in mm to MSL steps"""
        self.setStep(res*self.conv_factor)


    def findMaxAmpPos(self):
        # Finds the X and Y positions of maximum voltmeter amplitude
        # Function only used in "findCenter"
        index = np.unravel_index(np.argmax(np.abs(self.trans), axis=None), self.trans.shape)
        self.pos_x_center = self.xVals[index]
        self.pos_y_center = self.yVals[index]
        
    def findMinPhasePos(self):
        # Finds the X and Y positions of minimum voltmeter phase
        # Function only used in "findCenter"
        index = np.unravel_index(np.argmin(np.angle(self.trans), axis=None), self.trans.shape)
        self.pos_x_center = self.xVals[index]
        self.pos_y_center = self.yVals[index]

    def findCenterMM(self, minRes=None, , phaseAfter=None):
        """Runs a scan over the searchArea & finds maximum amplitude peak.

        Decreases range and resolution with each iteration until minRes in mm is reached"""
        if minRes:
            pass
        else:
            minRes = self.searchMinRes
            
        self.findCenter(minRes=minRes, phaseAfter=phaseAfter)


    def findCenter(self, minRes=500, phaseAfter=3):
        """Runs scan over area & finds maximum amplitude peak.
        Begins at arbitrary position and decreases range and resolution with each iteration.

        Takes a minimum resolution to search with in steps."""

        print("\nFinding center...")

        res = self.searchRes
        Range = self.searchRange
        self.pos_x_center = self.searchCenter[0]
        self.pos_y_center = self.searchCenter[1]
        

        search_iteration = 0

        while res >= minRes:
                
            print("  Search center : {:.3f}, Y {:.3f}".format(self.pos_x_center/self.conv_factor, self.pos_y_center/self.conv_factor))
            print("  Search range  : {:.2f}".format(Range/self.conv_factor))
            print("  Search res    : {:.3f}".format(res/self.conv_factor))
            print("  Min res       : {:.3f}".format(minRes/self.conv_factor))
            self.setRange(Range)
            self.setStep(res)

            self.moveToCenter()
            self.initScan(Range)
            self.scan(calibrate=False)
            search_iteration += 1
            if search_iteration < phaseAfter:
                self.findMaxAmpPos()
                print("Centering on max amplitude at X {:.3f}, Y {:.3f}".format(self.pos_x_center/self.conv_factor, self.pos_y_center/self.conv_factor))
            else:
                self.findMinPhasePos()
                print("Centering on min phase at X {:.3f}, Y {:.3f}".format(self.pos_x_center/self.conv_factor, self.pos_y_center/self.conv_factor))
            


            Range = Range / 5
            res = Range / 5
            if self.plotCenter:
                self.contour_plot_dB(name_elem="_{:d}".format(search_iteration))
                self.contour_plot_deg(name_elem="_{:d}".format(search_iteration))

        print("Found center at X {:.3f}, Y {:.3f}\n".format(self.pos_x_center/self.conv_factor, self.pos_y_center/self.conv_factor))
        self.setStep(self.Res)
        self.setRange(self.Range)

    def moveToCenter(self):
        if self._debug:
            print(" DEBUG: in moveToCenter()")
        # Moves MSL's to center position and sets new home position
        self.msl_x.moveAbs(int(self.pos_x_center))
        self.msl_y.moveAbs(int(self.pos_y_center))
        self.msl_x.hold()
        self.msl_y.hold()
        #self.msl_x.zero()
        #self.msl_y.zero()

    def initScan(self, Range=None):
        if self._debug:
            print(" DEBUG: in initScan(Range={})".format(Range))
        if Range==None:
            Range = self.Range

        # Get range parameters for scan
        self.setRange(Range)

        # Gets initial position
        self.pos_x = int(self.msl_x.getPos())
        self.pos_y = int(self.msl_y.getPos())

        # Moves to minimum position in range to begin scan
        self.msl_x.moveAbs(self.pos_x_min)
        self.msl_y.moveAbs(self.pos_y_min)
        self.msl_x.hold()
        self.msl_y.hold()

        # Create numpy arrays to store the data
        x = np.arange(self.pos_x_min, self.pos_x_max+self.Step, self.Step, dtype=float)
        y = np.arange(self.pos_y_min, self.pos_y_max+self.Step, self.Step, dtype=float)
        self.xVals, self.yVals = np.meshgrid(x, y)


        # reverse every other line in self.xVals
        self.xVals[1::2,:] = self.xVals[1::2,::-1]

        self.time = np.zeros_like(self.xVals, dtype=float)
        self.trans = np.zeros_like(self.xVals, dtype=complex)
        self.calVals = np.zeros_like(self.trans, dtype=complex)

        # VVM ready to begin collecting data
        self.vvm.trigger()


    def getTransmission(self):
        """Get the transmission from the VVM.  Loop if necessary to avoid
        one-off time out errors"""
        retry = 0
        while True:
            try:
                trans = self.vvm.getTransmission()
                break
            except pyvisa.VisaIOError:
                print("Visa Timeout Error, retrying twice")
                if retry < 2:
                    retry +=1
                    pass
                else:
                    # Re-raise the exception
                    raise
                    break
            except ValueError:
                pass
        return trans
        
    def getPowers(self):
        """Get the A and B powers from the VVM.  Loop if necessary to avoid
        one-off time out errors"""
        retry = 0
        while True:
            try:
                apow = float(self.vvm.getData(meas="APOW"))
                bpow = float(self.vvm.getData(meas="BPOW"))
                break
            except pyvisa.VisaIOError:
                print("Visa Timeout Error, retrying twice")
                if retry < 2:
                    retry +=1
                    pass
                else:
                    # Re-raise the exception
                    raise
                    break
            except ValueError:
                pass
        return apow, bpow


    def scan(self, calibrate=True):
        """Scan over the meshgrids of the stored xVals and yVals, and record data
        in trans.

        initScan will set up the xVals and yVals array as a regular raster scan grid.
        however, this methods will work with any scan pattern defined in those variables.

        If calibrate is True, the transmission at pos_x_center, pos_y_center will be
        recorded every self.calInterval points and stored in self.calVals"""
        if self._debug:
            print(" DEBUG: in scan(calibrate={})".format(calibrate))
        self.initTime()

        if self.CalInterval <= 0:
            calibrate = False

        lastCalValue = complex(0.,0.)

        if calibrate:
            self.moveToCenter()
            lastCalValue = self.getTransmission()

        for i, x in enumerate(self.xVals.ravel()):
            k = i
            y = self.yVals.ravel()[k]

            if calibrate:
                if abs(x-self.pos_x_center) < self.Step:
                    self.moveToCenter()
                    lastCalValue = self.getTransmission()

            if self.verbose:
                print("Moving to: X: {:.1f}, Y:{:.1f}".format(x, y))
            # Move to position
            self.msl_x.moveAbs(x)
            self.msl_y.moveAbs(y)
            self.msl_x.hold()
            self.msl_y.hold()

            # Gets positions and transmissions from VVM and loops in case of error
            self.xVals.ravel()[k] = self.msl_x.getPos()
            self.yVals.ravel()[k] = self.msl_y.getPos()
            self.trans.ravel()[k] = self.getTransmission()
            self.calVals.ravel()[k] = lastCalValue
            self.time.ravel()[k] = time.time() - self.start_time
            if self.verbose or (i % 10) == 0:
                print("    k: {:d}  X: {:.3f}, Y: {:.3f}, {:f} dB, {:f} deg".format(k, self.xVals.ravel()[k]/self.conv_factor, self.yVals.ravel()[k]/self.conv_factor, 20*np.log10(np.abs(self.trans.ravel()[k])), np.degrees(np.angle(self.trans.ravel()[k]))))

    def endSG(self):
        # Turns off signal generator output
        self.RF.off()
        self.LO.off()

    def spreadsheet(self):
        print("Writing data to spreadsheet...")

        x_data = self.xVals/self.conv_factor
        y_data = self.yVals/self.conv_factor
        trans_data = self.trans
        cal_data = self.calVals
        time_data = self.time

        if self.scan_type == "raster":
            # reverse every other line in self.xVals
            x_data[1::2,:] = x_data[1::2,::-1]
            y_data[1::2,:] = y_data[1::2,::-1]
            trans_data[1::2,:] = trans_data[1::2,::-1]
            cal_data[1::2,:] = cal_data[1::2,::-1]
            time_data[1::2,:] = time_data[1::2,::-1]

        outdata = np.array((x_data.ravel(), y_data.ravel(), trans_data.ravel().real, trans_data.ravel().imag, cal_data.ravel().real, cal_data.ravel().imag, time_data.ravel()), dtype='float')

        np.savetxt(self.save_name, outdata.transpose(), delimiter=", ")


    def contour_plot_dB(self, name_elem = None):
        """Plot a contour plot in dB of the beam pattern"""
        if not name_elem:
            name_elem = ""

        xi = np.linspace(self.pos_x_min/self.conv_factor, self.pos_x_max/self.conv_factor, 1000)
        yi = np.linspace(self.pos_y_min/self.conv_factor, self.pos_y_max/self.conv_factor, 1000)
        xi, yi = np.meshgrid(xi, yi)

        pts = np.array((self.xVals.ravel(), self.yVals.ravel())).transpose()

        zi = griddata(pts/self.conv_factor, 20*np.log10(np.abs(self.trans.ravel())), (xi, yi), method="linear")

        plt.clf() 
        CS = plt.contourf(xi, yi, zi)
        CL = plt.contour(xi, yi, zi, colors='k')
        plt.clabel(CL, colors='k')
        plt.xlabel("X Position (mm)")
        plt.ylabel("Y Position (mm)")
        matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
        plt.xlim(self.pos_x_min/self.conv_factor, self.pos_x_max/self.conv_factor)
        plt.ylim(self.pos_y_min/self.conv_factor, self.pos_y_max/self.conv_factor)
        plt.title("Amplitude vs. Position")
        plt.draw()
        plt.pause(0.001)
        plt.savefig("{}{}{}".format(self.save_name.split(".")[0], name_elem, "_dB.png"))


    def contour_plot_deg(self, name_elem = None):
        """Plot a contour plot in dB of the beam pattern"""
        if not name_elem:
            name_elem = ""

        xi = np.linspace(self.pos_x_min/self.conv_factor, self.pos_x_max/self.conv_factor, 1000)
        yi = np.linspace(self.pos_y_min/self.conv_factor, self.pos_y_max/self.conv_factor, 1000)
        xi, yi = np.meshgrid(xi, yi)

        pts = np.array((self.xVals.ravel(), self.yVals.ravel())).transpose()

        zi = griddata(pts/self.conv_factor, np.rad2deg(np.angle(self.trans.ravel())), (xi, yi), method="linear")
        
        plt.clf() 
        CS = plt.contourf(xi, yi, zi)
        CL = plt.contour(xi, yi, zi, colors='k')
        plt.clabel(CL, colors='k')
        plt.xlabel("X Position (mm)")
        plt.ylabel("Y Position (mm)")
        matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
        plt.xlim(self.pos_x_min/self.conv_factor, self.pos_x_max/self.conv_factor)
        plt.ylim(self.pos_y_min/self.conv_factor, self.pos_y_max/self.conv_factor)
        plt.title("Phase vs. Position")
        plt.draw()
        plt.pause(0.001)
        plt.savefig("{}{}{}".format(self.save_name.split(".")[0], name_elem, "_deg.png"))
        plt.show()

    def time_plot(self, file_name):
        # Makes time vs amplitude & phase plot given beamscanner data format, not spreadsheet data format
        amp_data = []
        phase_data = []

        f = open(str(file_name), 'r')
        lines = f.readlines()
        f.close()

        for i in range(len(lines) - 1):
            amp_data.append(float(lines[i+1].split()[3]))
            phase_data.append(float(lines[i+1].split()[4]))

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

    def y_plot(self, file_name):
        # Makes plot of amplitude & phase vs. Y-position along X = 0 plane
        x_data_all = []
        y_data_all = []
        y_data = []
        amp_data_all = []
        amp_data = []
        phase_data_all = []
        phase_data = []

        f = open(str(file_name), 'r')
        lines = f.readlines()
        f.close()

        for i in range(len(lines) - 1):
            x_data_all.append(float(lines[i+1].split()[1]))
            y_data_all.append(float(lines[i+1].split()[2]))
            amp_data_all.append(float(lines[i+1].split()[3]))
            phase_data_all.append(float(lines[i+1].split()[4]))

        for i in range(len(x_data_all)):
            if x_data_all[i] == 0:
                y_data.append(y_data_all[i])
                amp_data.append(amp_data_all[i])
                phase_data.append(phase_data_all[i])

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

    def x_plot(self, file_name):
        # Makes plot of amplitude & phase vs. X-position along Y = 0 plane
        x_data_all = []
        y_data_all = []
        x_data = []
        amp_data_all = []
        amp_data = []
        phase_data_all = []
        phase_data = []

        f = open(str(file_name), 'r')
        lines = f.readlines()
        f.close()

        for i in range(len(lines) - 1):
            x_data_all.append(float(lines[i+1].split()[1]))
            y_data_all.append(float(lines[i+1].split()[2]))
            amp_data_all.append(float(lines[i+1].split()[3]))
            phase_data_all.append(float(lines[i+1].split()[4]))

        for i in range(len(x_data_all)):
            if int(y_data_all[i]) == 0:
                x_data.append(x_data_all[i])
                amp_data.append(amp_data_all[i])
                phase_data.append(phase_data_all[i])

        fig, ax1 = plt.subplots()

        x_new = np.linspace(x_data[0], x_data[-1], num=len(x_data)*10)

        coefs_amp = poly.polyfit(x_data, amp_data, 2)
        fit_amp = poly.polyval(x_new, coefs_amp)
        ax1.plot(x_data, amp_data, 'bD', label = "Amp (meas)")
        ax1.plot(x_new, fit_amp, 'b--', label = "Amp (fitted)")
        ax1.set_xlabel("X position (mm)")
        ax1.set_ylabel("Amplitude (dB)", color='b')
        ax1.tick_params('y', colors='b')
        ax1.legend(loc = "upper left")

        coefs_phase = poly.polyfit(x_data, phase_data, 2)
        fit_phase = poly.polyval(x_new, coefs_phase)
        ax2 = ax1.twinx()
        ax2.plot(x_data, phase_data, 'r^', label = "Phase (meas)")
        ax2.plot(x_new, fit_phase, 'r-', label = "Phase (fitted)")
        ax2.set_ylabel('Phase (deg)', color='r')
        ax2.tick_params('y', colors='r')
        ax2.legend(loc = "upper right")

        fig.tight_layout()
        plt.show()


if __name__ == "__main__":

    # Begin
    bs = Beamscanner()
    bs.initTime()
    bs.readUSE()

    bs.verbose = False
    bs.plotCenter = False
    # Disable finding center for testing speed
    bs.centerBeforeScan = False

    # Establishes instrument communication
    rm = bs.initGPIB()
    bs.vvm = HP8508A.HP8508A(rm.open_resource("GPIB0::8::INSTR"))
    bs.RF = HMCT2240.HMCT2240(rm.open_resource("GPIB0::30::INSTR"))
    bs.LO = HP83630A.HP83630A(rm.open_resource("GPIB0::19::INSTR"))
    # For WIndows
    bs.msl_x = MSL.MSL(rm.open_resource("ASRL/dev/ttyUSB0::INSTR"), partyName="X")
    bs.msl_y = MSL.MSL(rm.open_resource("ASRL/dev/ttyUSB0::INSTR"), partyName="Y")

    # Initializes instruments
    bs.initSG()
    bs.initVVM()


    bs.initMSL()

    # Find center of beam to calibrate to
    bs.findCenterMM()

    # Preparing to scan
    print("Preparing for data ...")


    bs.initScan(bs.Range)

    # Scanning
    print("\nCollecting data...")
    bs.scan()

    # Finished scanning
    print("\nExecution time: " + str(time.time() - bs.start_time))
    # Don't turn off sig gens!
    # bs.endSG()
    bs.moveToCenter()

    # Writing to spread sheet
    bs.spreadsheet()

#   print("Plotting data ...")
    # Plots position vs. amplitude contour plot
#   bs.contour_plot(bs.save_name)
    # Plots amplitude and phase vs. time
#    bs.time_plot(bs.save_name)
    # Plots amplitude and phase vs. y position for slice at center of beam
#    bs.y_plot(bs.save_name)
    # Plots amplitude and phase vs. X position for slice at center of beam
#    bs.x_plot(bs.save_name)

    print("Deleting Beamscanner object")
    del bs
    print("Deleting Visa Resource Manager object")
    del rm

    print("\nEnd.")
