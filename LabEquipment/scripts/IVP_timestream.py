#! /usr/bin/env python
#
# This code runs a sweep from <max> to <min> with stepsize <step> and
# saves the data to <save_name>
#
# Usage: IVP_timestream.py <*config file> <file.dat> <sampleTime> <streamLength>

from LabEquipment.applications.mixer.IVP_timestream import *
import sys

def main():
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
