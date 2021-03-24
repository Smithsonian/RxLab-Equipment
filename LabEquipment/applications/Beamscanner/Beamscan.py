import pyvisa as visa
import os
import time
import sys
import numpy as np

import LabEquipment.drivers.Instrument.HP8508A as HP8508A
import LabEquipment.drivers.Instrument.HP83630A as HP83630A
import LabEquipment.drivers.Instrument.HMCT2240 as HMCT2240
import LabEquipment.drivers.Instrument.MSL as MSL
import LabEquipment.applications.Beamscanner.Beamscanner as Beamscanner

# Begin
bs = Beamscanner.Beamscanner()
bs.initTime()

cmd=None
use=None
# Read command line arguments
if len(sys.argv[1].split(".")) > 1:
    if sys.argv[1].split(".")[1] == "use":
        use = sys.argv.pop(1)

print(sys.argv)

if len(sys.argv) > 1:
    cmd = sys.argv[1]

bs.readUSE(useFile=use)

bs.printUSE()

bs.verbose = False
bs.plotCenter = True
bs.centerBeforeScan = False

# Establishes instrument communication
rm = bs.initGPIB(backend="@py")
bs.vvm = HP8508A.HP8508A(rm.open_resource("GPIB0::8::INSTR"))
bs.RF = HMCT2240.HMCT2240(rm.open_resource("GPIB0::30::INSTR"))
bs.LO = HP83630A.HP83630A(rm.open_resource("GPIB0::19::INSTR"))
# For WIndows
bs.msl_x = MSL.MSL(rm.open_resource("ASRL/dev/ttyUSB0::INSTR"), partyName="X")
bs.msl_y = MSL.MSL(rm.open_resource("ASRL/dev/ttyUSB0::INSTR"), partyName="Y")

if cmd == "Move":
    x = float(sys.argv[3])*bs.conv_factor
    y = float(sys.argv[4])*bs.conv_factor
    bs.centerBeforeScan = False
    bs.initMSL()
    bs.msl_x.moveAbs(x)
    bs.msl_y.moveAbs(y)
    bs.msl_x.hold()
    bs.msl_y.hold()
elif cmd == "SetFreqs":
    bs.verbose = True
    bs.calcFreqs()
    bs.initSG()
    bs.initVVM()
    trans = bs.getTransmission()
    print("VVM transmission: {:.2f} dB, {:.2f} deg".format(20*np.log10(np.abs(trans)), np.rad2deg(np.angle(trans))))
    pows = bs.getPowers()
    print("VVM powers: A(ref) {:.2f} dBm, B {:.2f} dBm".format(pows[0], pows[1]))

else: # cmd == None or Center
    # Initializes all instruments
    bs.initSG()
    bs.initVVM()

    bs.initMSL()

    if cmd == "Center":
        #bs._debug = True
        bs.centerBeforeScan = True
        bs.findCenterMM()
        bs.moveToCenter()
    else:
        print("Preparing for scan ...")

        bs.initScan(bs.Range)
        # Scanning
        print("\nCollecting data...")
        bs.scan()
        # Finished scanning
        print("\nExecution time: " + str(time.time() - bs.start_time))

        bs.moveToCenter()

        # Writing to spread sheet
        bs.spreadsheet()

        print("Plotting data ...")
        bs.contour_plot_dB()
        bs.contour_plot_deg()

del bs
del rm

print("\nEnd.")
