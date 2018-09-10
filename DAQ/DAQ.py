##################################################
#                                                #
# Driver for DAQ devices                         #
#                                                #
# Larry Gardner, July 2018                       #         
#                                                #
##################################################

from uldaq import *
from os import system
from sys import stdout
from time import sleep
import numpy as np
import time

class DAQ:
    def __init__(self, AiMode=AiInputMode.DIFFERENTIAL):
        self.device = None
        
        self.interface_type = InterfaceType.USB
        self.AiMode = AiMode
        self.AiRange = 0
        self.sleepTime = 0.01
        
    def listDevices(self):
        try:
            self.device = get_daq_device_inventory(self.interface_type)
            self.number_of_devices = len(self.device)
            if self.number_of_devices == 0:
                raise Exception('Error: No DAQ devices found')
            print("Found {:d} DAQ device(s): ".format(self.number_of_devices))
            for i in range(self.number_of_devices):
                print("    {:s} ({:s})".format(self.device[i].product_name, self.device[i].unique_id))
        except (KeyboardInterrupt, ValueError):
            print("Could not find DAQ device(s).")
        
    def connect(self,Boardnum = 0):
        # Connects to DAQ device
        try:
            self.device = get_daq_device_inventory(self.interface_type)
            self.daq_device = DaqDevice(self.device[Boardnum])
            # Connect to DAQ device
            descriptor = self.daq_device.get_descriptor()
            self.daq_device.connect()
            print("Connected to {:s}".format(descriptor.dev_string))
        except (KeyboardInterrupt, ValueError):
            print("Could not connect DAQ device.")
        
        # Get some basic info on the device
        self.ai_device = self.daq_device.get_ai_device()
        self.ai_info = self.ai_device.get_info()
        self.numChannels()
        
        self.ao_device = self.daq_device.get_ao_device()
        self.ao_info = self.ao_device.get_info()
        
        self.dio_device = self.daq_device.get_dio_device()
        
        # Get the port types for the device(AUXPORT, FIRSTPORTA, ...)
        self.dio_info = self.dio_device.get_info()
        self.port_types = self.dio_info.get_port_types()
        
        
    def disconnect(self, Boardnum = 0):
        # Disconnects DAQ device
        if self.daq_device:
            if self.daq_device.is_connected():
                self.daq_device.disconnect()
                print("DAQ device {:s} is disconnected.".format(self.device[Boardnum].product_name))
            print("DAQ device {:s}".format(self.device[Boardnum].product_name))
            self.daq_device.release()
            
    def name(self, index = 0):
        name = self.device[index].product_name
        return name
        
    def numChannels(self):
        """Use the SINGLE_ENDED input mode to get the number of channels.
        # If the number of channels is greater than zero, then the device
        # supports the SINGLE_ENDED input mode; otherwise, the device only
        # supports the DIFFERENTIAL input mode."""
        self.number_of_channels = self.ai_info.get_num_chans_by_mode(AiInputMode.SINGLE_ENDED)
        if self.number_of_channels > 0:
            if self.AiMode != AiInputMode.DIFFERENTIAL:
                self.AiMode = AiInputMode.SINGLE_ENDED
        else:
            self.AiMode = AiInputMode.DIFFERENTIAL
    
    def setAiRange(self, r):
        """Sets the AI Range to the index r in the list of ranges returned by self.AiInfo.get_ranges(self.AiMode)"""
        ranges = self.getAiRanges()
        if r < len(ranges):
            self.AiRange = ranges[r]
            
    def getAiRangeIndex(self):
        """Returns the index of the current AiRange in the list of self.AiInfo.get_ranges(self.AiMode)"""
        ranges = self.getAiRanges()
        return ranges.index(self.AiRange)
        
    def getAiRanges(self):
        """Returns the list of valid ranges for this DAQ"""
        return self.ai_info.get_ranges(self.AiMode)
    
    def AIn(self,channel = 0):
        # Reads input analog data from specified channel
        if channel > self.number_of_channels:
            channel = self.number_of_channels - 1
            
        ranges = self.ai_info.get_ranges(self.AiMode)
        
        data = self.ai_device.a_in(channel, self.AiMode, self.AiRange, AInFlag.DEFAULT)
        return data
        
    def AOut(self, data, channel = 0):
        # Write output analog data to specified channel
        output_range = self.ao_info.get_ranges()[0]
        self.ao_device.a_out(channel, output_range, AOutFlag.DEFAULT, data)
        
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
