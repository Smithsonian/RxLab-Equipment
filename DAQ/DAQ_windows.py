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
import time

# Stop InstaCal configurations being used to manage DAQ devices
ignore_instacal()

class DAQ:
    def __init__(self, AiMode=enums.AnalogInputMode.DIFFERENTIAL):
        self.device = None
        
        self.interface_type = enums.InterfaceType.USB
        self.AiMode = AiMode
        self.AiRange = 0
		self.AoRange = 0
        self.sleepTime = 0.01
        
    def listDevices(self):
        try:
            self.device = get_daq_device_inventory(self.interface_type)
            self.number_of_devices = len(self.device)
            if self.number_of_devices == 0:
                raise RunTimeException('Error: No DAQ devices found')
            print("Found {:d} DAQ device(s): ".format(self.number_of_devices))
            for i in range(self.number_of_devices):
                print("    {:s} ({:s})".format(self.device[i].product_name, self.device[i].unique_id))
        except (KeyboardInterrupt, ValueError):
            print("Could not find DAQ device(s).")
        
    def connect(self, Boardnum = 0):
        # Connects to DAQ device
        try:
			# Search for devices to get the DAQ ids
            self.device = get_daq_device_inventory(self.interface_type)
			# Register the board with mcculw
			create_daq_device(Boardnum, self.device[Boardnum])
			# Check the board number of the device exists
			self.daq_device = get_board_number(self.devices[Boardnum])
			
            # Connect to DAQ device
            descriptor = self.device[Boardnum]
            print("Connected to {:s} : {:s}".format(descriptor.dev_string. descriptor.unique_id))
        except (KeyboardInterrupt, ValueError):
            print("Could not connect DAQ device.")
        
        # Get some basic info on the device
        self.numChannels()
		
		# Set the Ai Input mode to that specified in __init__
		self.setAiMode(self.AiMode)
		
		self.getAiRange()
		self.getAoRange()
        
        
            
    def name(self, index = 0):
        name = self.device[index].product_name
        return name
        
    def numChannels(self):
        """Get the number of channels and the AI"""
        self.number_of_channels = get_config(enums.InfoType.BOARDINFO, self.daq_device, 0, enums.BoardInfo.NUMADCHANS)
		
	def getAiInfo(self):
		"""Get miscellaneous AI information and store it in a struct"""
		
		
	def setAiMode(self, mode):
		"""Sets the AiMode to one of the modes in enums.AnalogInputMode"""
		a_input_mode(self.daq_device, mode)
		
	def getAiMode(self):
		"""Getes the AiMode for the current daq device"""
		self.AiMode = enums.AnalogInputMode(get_config(enums.InfoType.BOARDINFO, self.daq_device, 0, enums.BoardInfo.ADAIMODE))
		return self.AiMode
    
    def setAiRange(self, range):
        """Sets the AI Range to one of the ranges in enums.ULRange"""
		set_config(enums.InfoType.BOARDINFO, self.daq_device, 0, enums.BoardInfo.RANGE, range)
            
    def getAiRangeIndex(self):
        """Returns the index of the current AiRange in the list of self.AiInfo.get_ranges(self.AiMode)"""
		return self.AiRange._value
        
    def getAiRange(self):
        """Returns the current range of the DAQ"""
        self.AiRange = enums.ULRange(get_config(enums.InfoType.BOARDINFO, self.daq_device, 0, enums.BoardInfo.RANGE))
		return self.AiRange
    
	def setAoRange(self, range):
        """Sets the AI Range to one of the ranges in enums.ULRange"""
		set_config(enums.InfoType.BOARDINFO, self.daq_device, 0, enums.BoardInfo.DACRANGE, range)
            
    def getAoRangeIndex(self):
        """Returns the index of the current AiRange in the list of self.AiInfo.get_ranges(self.AiMode)"""
		return self.AoRange._value
        
    def getAoRange(self):
        """Returns the current range of the DAQ"""
        self.AoRange = enums.ULRange(get_config(enums.InfoType.BOARDINFO, self.daq_device, 0, enums.BoardInfo.DACRANGE))
		return self.AoRange
    
	
    def AIn(self, channel = 0):
        """Reads input analog data from specified channel - returns value in volts"""
        if channel > self.number_of_channels:
            raise ValueError("channel index requested is higher than number of channels")
        data = v_in(self.daq_device, channel, self.AiRange)
        return data
        
    def AOut(self, data, channel = 0):
		"""Write output analog data to the specified channel.  Value is in volts"""
		if channel > self.number_of_channels:
            raise ValueError("channel index requested is higher than number of channels")
        
        # Write output analog data to specified channel
        v_out(self.daq_device, channel, self.AoRange, data)
        
    def DOut(self, data, channel = 0):
        # Write output digital data to specified channel
        self.port_to_write = self.port_types[0]

        # Configure port
        self.dio_device.d_config_port(self.port_to_write, DigitalDirection.OUTPUT)

        # Writes output for bit
        self.dio_device.d_bit_out(self.port_to_write, channel, data)
    
    def AInScan(self, low_channel, high_channel, rate, samples_per_channel, scan_time = None):
        """Runs a scan across multiple channels, with multiple samples per channel.  Returns a numpy array of
        shape (samples_per_channel, channel_count)"""
        # Verify that the specified device supports hardware pacing for analog input.
        if not self.ai_info.has_pacer():
            raise Exception('Error: The specified DAQ device does not support hardware paced analog input')
                
        # Verify the high channel does not exceed the number of channels, and
        # set the channel count.
        if high_channel >= self.number_of_channels:
            high_channel = self.number_of_channels - 1
        channel_count = high_channel - low_channel + 1
        
        # Allocate a buffer to receive the data.
        data = create_float_buffer(channel_count, samples_per_channel)
        
        # Start the acquisition.
        self.ai_device.a_in_scan(low_channel, high_channel, self.AiMode, self.AiRange, samples_per_channel,
                                        rate, ScanOption.CONTINUOUS, AInScanFlag.DEFAULT, data)
        
        start_time = time.time()
        
        # Set scan time to a high number of seconds if it isn't set
        if scan_time == None:
            scan_time = 500000
        
        while (time.time() - start_time) <= scan_time:
            # Get the status of the background operation
            status, transfer_status = self.ai_device.get_scan_status()
            index = transfer_status.current_index

            # Check to see if we are done
            if transfer_status.current_scan_count >= samples_per_channel:
                break

            sleep(self.sleepTime)          
        
        if self.daq_device:
            # Stop the acquisition if it is still running.
            if status == ScanStatus.RUNNING:
                self.ai_device.scan_stop()                
        
        d = np.array(data)
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
