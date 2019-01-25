#! /usr/bin/env python
#                                                #
# Load Mover object and code for testing         #
#                                                #
# Based on code by Larry Gardner, July 2018      #
# Paul Grimes, January 2019                      #
#                                                #
##################################################

from __future__ import print_function, division

import pprint
from time import sleep
from pkg_resources import resource_filename

import LabEquipment.drivers.DAQ.DAQ as DAQ
from LabEquipment.applications.mixer import _default_LoadMover_config

class LoadMover(object):
    def __init__(self, config=None, configFile=None, verbose=False, vverbose=False):
        """Class for driving the ambient load mover"""
        self.verbose = verbose
        self.vverbose = vverbose

        self.daq = DAQ.DAQ(autoConnect=False, verbose=self.vverbose)

        self.config = None
        self.setConfig(_default_LoadMover_config.defaultConfig)

        if self.vverbose:
            print("LoadMover.__init__: Default Config Loaded: Current config:")
            pprint.pprint(self.config)

        if configFile != None:
            self.readConfig(configFile)
            if self.vverbose:
                print("LoadMover.__init__: Config Loaded from: {:s}".format(configFile))
                pprint.pprint(self.config)

        if config != None:
            if self.vverbose:
                print("LoadMover.__init__: Config passed to __init__:")
                pprint.pprint(config)

            self.setConfig(config)

            if self.vverbose:
                print("LoadMover.__init__: Config now:")
                pprint.pprint(self.config)

        if self.vverbose:
            print("LoadMover.__init__: Done setting configFile and config: Current config:")
            pprint.pprint(self.config)

        self.initDAQ()


    def readConfig(self, filename):
        """Read the .hjson configuration file to set up the LoadMover unit."""
        # Opens use file
        self.configFile = filename

        if self.verbose:
            print("LoadMover.readConfig: Reading config file: ", self.configFile)
        newConfig = hjsonConfig.hjsonConfig(filename=filename, verbose=self.vverbose)
        if self.vverbose:
            print("LoadMover.readConfig: Read config: ")
            pprint.pprint(newConfig)
        self.setConfig(newConfig)

    def setConfig(self, config):
        """Merge a new config into the existing config.

        Called automatically from readFile()"""
        if self.vverbose:
            print("LoadMover.setConfig: Merging New config:")
            pprint.pprint(config)
        self.config = hjsonConfig.merge(self.config, config)
        if self.vverbose:
            print("LoadMover.setConfig: Merged Config:")
            pprint.pprint(self.config)
        self._applyConfig()

    def _applyConfig(self):
        """Apply the configuration to set up the object variables.  Will get
        called automatically from setConfig

        This should be overridden to read any additional configuration values
        when subclassing LoadMover.py"""
        try:
            self.daq.setConfig(self.config["daq"])
        except KeyError:
            pass

        try:
            self.boardnum = self.config["boardnum"]
            self.controlBit = self.config["control-bit"]
            self.loadInState = self.config["load-in"]
            self.switchTime = self.config["switch-time"]
        except KeyError:
            if self.verbose:
                print("Got KeyError while applying LoadMover config")
                pprint.pprint(self.config)
            raise

    def __delete__(self):
        """Run this before deleting the LoadMover object, to release the DAQ board"""
        self.endDAQ()

    def initDAQ(self):
        """Lists available DAQ devices, connects the selected board and sets the AI Range"""
        self.daq.connect()

    def endDAQ(self):
        """Disconnects and releases selected board number"""
        self.daq.disconnect()

    def setLoadPosition(self, bitState):
        """Set the load position bit to chosen state"""
        self.daq.DOut(bitState, channel=self.controlBit)
        sleep(self.switchTime)

    def loadIn(self):
        """Put the load into the beam"""
        self.setLoadPosition(self.loadInState)

    def loadOut(self):
        """Put the load into the beam"""
        self.setLoadPosition(not self.loadInState)

if __name__ == "__main__":
    # This code sets the load position to the given bit state
    #
    # Usage: python3 <*config file> <bit state>

    test = LoadMover(verbose=True, vverbose=False)

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

    print("Load control bit set to {:}".format(loadPos)
