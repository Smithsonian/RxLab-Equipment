#! /usr/bin/env python
#
# This code runs a sweep from <max> to <min> with stepsize <step> and
# saves the data to <save_name>
#
# Usage: IVP.py <*config file> <file.dat> <min> <max> <step>

from LabEquipment.applications.mixer.IVY import *
import sys

def main():
    # This code runs a sweep from <max> to <min> with stepsize <step> and
    # saves the data to <save_name>, taking Y factors and Noise temperatures.
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
    test.plot2()
    # Wait until the plot is done
    try:
        save = input("Save Plots? [Y/N]")
        if save =="Y":
            test.savefig()
    except SyntaxError:
        pass


    # Close down the IV object cleanly, releasing the DAQ and PM
    del test

    print("End.")
