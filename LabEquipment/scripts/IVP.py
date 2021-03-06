#! /usr/bin/env python
#
# This code runs a sweep from <max> to <min> with stepsize <step> and
# saves the data to <save_name>
#
# Usage: IVP.py <*config file> <file.dat> <min> <max> <step>

from LabEquipment.applications.mixer.IVP import *
import sys

def main():
    if len(sys.argv) == 6 or len(sys.argv) == 2:
        confFile = sys.argv.pop(1)
    else:
        confFile = "IVP-config.hjson"

    test = IVP(configFile=confFile, verbose=True, vverbose=False)

    if len(sys.argv) >= 5:
        test.save_name = sys.argv[1]
        test.sweepmin = float(sys.argv[2])
        test.sweepmax = float(sys.argv[3])
        test.step = float(sys.argv[4])
    else:
        try:
            sweepConf = test.config["sweep"]
        except KeyError:
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
