##################################################
#                                                #
# Driver for DAQ devices using the MCC UL        #
# for Windows									 #
#                                                #
# Import this via the DAQ.py wrapper that        #
# selects which of DAQ_windows and DAQ_linux to  #
# import.										 #
#												 #
# Note that the windows version works somewhat   #
# differently to the object orientated linux     #
# version.  									 #
#                                                #
# Larry Gardner, July 2018						 #
# Paul Grimes, Oct, 2018                         #
#                                                #
##################################################

from mcculw.ul import *
from mcculw import enums
from time import sleep
import numpy as np
import ctypes

# Stop InstaCal configurations being used to manage DAQ devices
ignore_instacal()

# Define some nearly empty classes for holding data
class Struct(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class AiInfo(Struct):
    def get_ranges(self):
        """Ignores AiMode, as AiInfo.ranges is filled according to device type and mode.
        Object kept for compatibility."""
        return self.ranges
    def has_pacer(self):
        return self._has_pacer

class AoInfo(Struct):
    def get_ranges(self):
        """AoInfo.ranges is filled according to device type and mode."""
        return self.ranges

class DioInfo(Struct):
    def get_port_types():
        """DioInfo.port_types is filled according to device type"""

# For handling memory pointers
def memhandle_as_ctypes_array_scaled(memhandle):
    return ctypes.cast(memhandle, ctypes.POINTER(ctypes.c_double))

class DAQ:
    """A DAQ object representing a MCC DAQ device.

    Differences from Linux version:
        self.daq_device contains the DaqDeviceDescriptor for the
        connect DAQ board, rather than the Daq object.  In combination with self.boardnum,
        this contains all the information available for connnections.
    """
    def __init__(self, autoConnect=True, boardnum=0, AiMode=enums.AnalogInputMode.DIFFERENTIAL, verbose=True):
        """Create the DAQ device, and if autoConnect, automatically connect to
        board number 0"""
        self.devices = None
        self.daq_device = None
        self.boardnum = None
        self.verbose = verbose

        self.interface_type = enums.InterfaceType.USB
        self.AiMode = AiMode
        self.AiInfo = AiInfo()
        self.AoInfo = AoInfo()
        self.AiRange = None
		self.AoRange = None

        # Time to sleep between checks in AInScan
        self.sleepTime = 0.01

        if autoConnect:
            self.connect(boardnum)


    def listDevices(self):
        try:
            self.devices = get_daq_device_inventory(self.interface_type)
            self.number_of_devices = len(self.devices)
            if self.number_of_devices == 0:
                raise RunTimeException('Error: No DAQ devices found')
            if self.verbose:
                print("Found {:d} DAQ device(s): ".format(self.number_of_devices))
                for i in range(self.number_of_devices):
                    print("    {:s} ({:s})".format(self.devices[i].product_name, self.devices[i].unique_id))
        except (KeyboardInterrupt, ValueError):
            print("Could not find DAQ device(s).")

    def connect(self, boardnum=0):
        # Connects to DAQ device
        try:
			# Search for devices to get the DAQ ids
            if self.devices == None:
                self.listDevices()
			# Register the board with mcculw and store the descriptor internally
			create_daq_device(boardnum, self.devices[boardnum])
			self.daq_device = self.devices[boardnum]
            self.boardnum = boardnum
            if self.verbose:
                print("Connected to {:s} : {:s}".format(self.daq_device.dev_string. self.daq_device.unique_id))
        except (KeyboardInterrupt, ValueError):
            print("Could not connect to DAQ device {:d}.".format(boardnum))

        # Get some basic info on the device
        self.numChannels()
        self.getAiInfo()
        self.getAoInfo()

		# Set the Ai Input mode to that specified in __init__
		self.setAiMode(self.AiMode)

		self.getAiRange()
		self.getAoRange()


    def name(self, index=0):
        if self.daq_device != None:
            name = self.daq_device.product_name
        else:
            name = None
        return name

    def numChannels(self):
        """Get the number of channels and the AI"""
        self.number_of_channels = get_config(enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.NUMADCHANS)

    def _get_supports_scan(self):
        """From mcculw.examples.props.ai.py

        Tests to see if the DAQ device supports scanning i.e. has a hardward pacer"""
        try:
            get_status(self.boardnum, enums.FunctionType.AIFUNCTION)
        except ULError:
            return False
        return True

    def _get_available_ranges(self, ad_resolution):
        result = []

        # Check if the board has a switch-selectable, or only one, range
        hard_range = get_config(
            enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.RANGE)

        if hard_range >= 0:
            result.append(enums.ULRange(hard_range))
        else:
            for ai_range in enums.ULRange:
                try:
                    if ad_resolution <= 16:
                        a_in(self.boardnum, 0, ai_range)
                    else:
                        a_in_32(self.boardnum, 0, ai_range)
                    result.append(ai_range)
                except ULError as e:
                    if (e.errorcode == enums.ErrorCode.NETDEVINUSE or
                            e.errorcode == enums.ErrorCode.NETDEVINUSEBYANOTHERPROC):
                        raise

        return result

    def _get_resolution(self):
        return get_config(
            enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.ADRES)

	def getAiInfo(self):
		"""Get miscellaneous AI information and store it in a struct

        We hard code the allowed ranges for the USB-1408 because mcculw can't
        tells us which are allowed"""
        self.AiInfo._has_pacer = self._get_supports_scan()
        self.AiInfo._ad_resolution = self._get_resolution()
        self.AiInfo.ranges = self._get_available_ranges(self.AiInfo._ad_resolution)

    def getAoInfo(self):
		"""Get miscellaneous AO information and store it in a struct

        We hard code the allowed ranges for the USB-1408 because mcculw can't
        tells us which are allowed"""
        if self.name().startswith("USB-1408") or self.name().startswith("USB-1208"):
            self.AoInfo.ranges = {enums.ULRange.UNI5VOLTS.value:enums.ULRange.UNI5VOLTS}

    def getDioInfo(self):
		"""Get miscellaneous DIO information and store it in a struct

        We hard code the port types for the USB-1408 because mcculw can't
        tells us which are allowed"""
        if self.name().startswith("USB-1408") or self.name().startswith("USB-1208"):
            self.DioInfo.port_types = {
                        enums.DigitalPortType.FIRSTPORTA.value:enums.DigitalPortType.FIRSTPORTA,
                        enums.DigitalPortType.FIRSTPORTB.value:enums.DigitalPortType.FIRSTPORTB,
                        }

	def setAiMode(self, mode):
		"""Sets the AiMode to one of the modes in enums.AnalogInputMode"""
		a_input_mode(self.boardnum, mode)

	def getAiMode(self):
		"""Getes the AiMode for the current daq device"""
		self.AiMode = enums.AnalogInputMode(get_config(enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.ADAIMODE))
		return self.AiMode

    def setAiRange(self, range):
        """Sets the AI Range to one of the ranges in enums.ULRange"""
		set_config(enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.RANGE, range)
        self.AiMode = range

    def getAiRangeIndex(self):
        """Returns the id of the current AiRange in the list of self.AiInfo.get_ranges(self.AiMode)"""
		return self.AiRange._value

    def getAiRange(self):
        """Returns the current range of the DAQ"""
        self.AiRange = enums.ULRange(get_config(enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.RANGE))
		return self.AiRange

	def setAoRange(self, range):
        """Sets the AI Range to one of the ranges in enums.ULRange"""
		set_config(enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.DACRANGE, range)
        self.AoRange = range

    def getAoRangeIndex(self):
        """Returns the id of the current AiRange in the list of self.AiInfo.get_ranges(self.AiMode)"""
		return self.AoRange._value

    def getAoRange(self):
        """Returns the current range of the DAQ"""
        self.AoRange = enums.ULRange(get_config(enums.InfoType.BOARDINFO, self.boardnum, 0, enums.BoardInfo.DACRANGE))
		return self.AoRange

    def AIn(self, channel = 0):
        """Reads input analog data from specified channel - returns value in volts"""
        if channel > self.number_of_channels:
            raise ValueError("channel index requested is higher than number of channels")
        if channel < 0:
            raise ValueError("channel index must be 0 or positive")

        data = v_in(self.boardnum, channel, self.AiRange)
        return data

    def AOut(self, data, channel=0):
		"""Write output analog data to the specified channel.  Value is in volts"""
		if channel > self.number_of_channels:
            raise ValueError("channel index requested is higher than number of channels")
        if channel < 0:
            raise ValueError("channel index must be 0 or positive")

        # Write output analog data to specified channel
        v_out(self.boardnum, channel, self.AoRange, data)

    def DOut(self, data, channel=0, port=enums.DigitalPortType.FIRSTPORTA):
        """Write output digital data to specified channel"""
        # Look up port in DioInfo - will raise value error if port doesn't exist
        port_to_write = self.DioInfo.port_types[port.value]

        # Configure port
        d_config_port(self.boardnum, port_to_write, enums.DigitalDirection.OUTPUT)

        # Writes output for bit
        d_bit_out(self.boardnum, port_to_write, channel, data)

    def AInScan(self, low_channel, high_channel, rate, samples_per_channel, scan_time = None):
        """Runs a scan across multiple channels, with multiple samples per channel.  Returns a numpy array of
        shape (samples_per_channel, channel_count)"""
        # Verify that the specified device supports hardware pacing for analog input.
        if not self.AiInfo.has_pacer():
            raise Exception('Error: The specified DAQ device does not support hardware paced analog input')

        # Verify the high channel does not exceed the number of channels, low channel is
        #0 or positive and set the channel count.
        if high_channel >= self.number_of_channels:
            high_channel = self.number_of_channels - 1
        if low_channel < 0:
            low_channel = 0
        channel_count = high_channel - low_channel + 1

        # Allocate a buffer to receive the data.
        total_count = channel_count*samples_per_channel
        data = scaled_win_buf_alloc(total_count)

        # Set up the scan options
        scan_options = (enums.ScanOption.CONTINUOUS | enums.ScanOption.SCALEDATA  | enums.ScanOption.BACKGROUND)

        # Start the acquisition.
        a_in_scan(self.boardnum, low_channel, high_channel, samples_per_channel,
                                        rate, data, self.AiRange,
                                        scan_options)

        status, curr_count, curr_index = get_status(
                    self.boardnum, enums.FunctionType.AIFUNCTION)

        while status != enums.Status.IDLE:
            sleep(self.sleepTime)
            # Get the status of the background operation
            status, curr_count, curr_index = get_status(
                    self.boardnum, enums.FunctionType.AIFUNCTION)

            # Check to see if we are done
            if curr_count >= total_count:
                break



        stop_background(self.boardnum, enums.FunctionType.AIFUNCTION)

        d = np.array(data)
        win_buf_free(data)
        d = d.reshape((samples_per_channel, channel_count))

        return d


if __name__ == "__main__":
    daq = DAQ()
    daq.listDevices()
    daq.connect()
    daq.setAiRange(5)
    data = daq.AIn(0)
    print(data)
    data = daq.AInScan(0,1,10000,1000,1)
    print(data)
    daq.DOut(1)
    daq.disconnect()
