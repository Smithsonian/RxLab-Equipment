#! /usr/bin/env python
#                                                #
# Analog temperature sensor object and code for  #
# testing                                        #
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
from LabEquipment.applications.mixer import _default_TempSensor_config

class TempSensor(object):
    def __init__(self):
        pass
    def getT(self):
        """Return the temperature"""
        return 292.5
