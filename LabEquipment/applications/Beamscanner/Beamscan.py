import visa
import os
import time
import sys

import LabEquipment.drivers.Instrument.HP8508A as HP8508A
import LabEquipment.drivers.Instrument.HP83630A as HP83630A
import LabEquipment.drivers.Instrument.HMCT2240 as HMCT2240
import LabEquipment.drivers.Instrument.MSL as MSL
import LabEquipment.applications.Beamscanner.Beamscanner as Beamscanner

# Begin
bs = Beamscanner.Beamscanner()
bs.initTime()
bs.readUSE()



bs.verbose = False
bs.plotCenter = False
bs.centerBeforeScan = False

# Establishes instrument communication
rm = bs.initGPIB(backend="@ni")
bs.vvm = HP8508A.HP8508A(rm.open_resource("GPIB0::8::INSTR"))
bs.RF = HMCT2240.HMCT2240(rm.open_resource("GPIB0::30::INSTR"))
bs.LO = HP83630A.HP83630A(rm.open_resource("GPIB0::19::INSTR"))
# For WIndows
bs.msl_x = MSL.MSL(rm.open_resource("ASRL4::INSTR", baud_rate=9600, data_bits=8, parity=visa.constants.Parity.none, stop_bits=visa.constants.StopBits.one, flow_control=0), partyName="X")
bs.msl_y = MSL.MSL(rm.open_resource("ASRL4::INSTR", baud_rate=9600, data_bits=8, parity=visa.constants.Parity.none, stop_bits=visa.constants.StopBits.one, flow_control=0), partyName="Y")

# Read command line arguments
if len(sys.argv) > 1:
    cmd = sys.argv[1]
else:
    cmd = None

if cmd == "Move":
    x = float(sys.argv[2])/bs.conv_factor
    y = float(sys.argv[3])/bs.conv_factor
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

else: # cmd == None or Center
    # Initializes all instruments
    bs.initSG()
    bs.initVVM()

    bs.initMSL()

    if cmd == "Center":
        bs.findCenterMM()
        bs.moveToCenter()
    else:
        print("Preparing for scan ...")
        if bs.centerBeforeScan:
            bs.findCenterMM()
        bs.initScan(bs.Range)
        # Scanning
        print("\nCollecting data...")
        bs.scan()
        # Finished scanning
        print("\nExecution time: " + str(time.time() - bs.start_time))

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

del bs
del rm

print("\nEnd.")
