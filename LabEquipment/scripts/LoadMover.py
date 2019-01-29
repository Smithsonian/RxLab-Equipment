#! /usr/bin/env python
#
# This code sets the load position to the given bit state
#
# Usage: python3 <*config file> <bit state>

from LabEquipment.applications.mixer.LoadMover import *

def main():
    if len(sys.argv) == 3:
        confFile = sys.argv.pop(1)
    else:
        confFile = "LoadMover-config.hjson"

    test = LoadMover(configFile=confFile, verbose=True, vverbose=False)

    if len(sys.argv) == 2:
        loadPos = sys.argv[1]
    else:
        loadPos = input("Set load control bit state:")

    # Run a sweep
    test.setLoadPosition(loadPos)

    print("Load control bit set to {:}".format(loadPos))
