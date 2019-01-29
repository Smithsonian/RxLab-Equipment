#! /usr/bin/env python
#
# This code runs an IF sweep from <max> to <min> with stepsize <step> and
# saves the data to <save_name>, taking Y factors and Noise temperatures
#
# Usage: IFY.py <*config file> <file.dat> <min> <max> <step>

from LabEquipment.applications.mixer.IFY import *
import sys

def main():
    # This code runs an IF sweep from <max> to <min> with stepsize <step> and
    # saves the data to <save_name>, taking Y factors and Noise temperatures.
    #
    # Usage: python3 <file.dat> <min> <max> <step> <*use file>

    if len(sys.argv) == 6 or len(sys.argv) == 2:
        confFile = sys.argv.pop(1)
    else:
        confFile = "IFY-config.hjson"

    test = IFY(configFile=confFile, verbose=True, vverbose=False)

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
            test.sweepmin = float(input("Minimum Frequency [GHz]: "))
            test.sweepmax = float(input("Maximum Frequency [GHz] "))
            test.step = float(input("Step [GHz]: "))

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
