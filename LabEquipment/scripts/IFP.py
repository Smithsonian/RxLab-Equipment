#! /usr/bin/env python
#
# This code runs a YIG filter sweep from <min> to <max> with stepsize <step> and
# saves the data to <save_name>
#
# Usage: IFP.py <*config file> <file.dat> <min> <max> <step>

from LabEquipment.applications.mixer.IFP import *
import sys

def main():
    if len(sys.argv) == 6 or len(sys.argv) == 2:
        confFile = sys.argv.pop(1)
    else:
        confFile = "IFP-config.hjson"

    test = IFP(configFile=confFile, verbose=True, vverbose=False)

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
            test.sweepmin = float(input("Minimum frequency [GHz]: "))
            test.sweepmax = float(input("Maximum frequency [GHz]: "))
            test.step = float(input("Step [GHz]: "))


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
