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
import time

class DAQ:
    def __init__(self):
        self.device = None
        
        self.interface_type = InterfaceType.USB
        
    def listDevices(self):
        try:
            self.device = get_daq_device_inventory(self.interface_type)
            self.number_of_devices = len(self.device)
            if self.number_of_devices == 0:
                raise Exception('Error: No DAQ devices found')
            print("\nFound " + str(self.number_of_devices) + " DAQ device(s): ")
            for i in range(self.number_of_devices):
                print("    ",self.device[i].product_name, " (", self.device[i].unique_id, ")", sep="")
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
            print("\nConnected to ", descriptor.dev_string,"\n")
        except (KeyboardInterrupt, ValueError):
            print("Could not connect DAQ device.")
            
    def disconnect(self, Boardnum = 0):
        # Disconnects DAQ device
        if self.daq_device:
            if self.daq_device.is_connected():
                self.daq_device.disconnect()
                print("\nDAQ device", self.device[Boardnum].product_name, "is disconnected.")
            print("DAQ device", self.device[Boardnum].product_name, "is released.")
            self.daq_device.release()
            
    def name(self, index = 0):
        name = self.device[index].product_name
        return name
    
    def AIn(self,channel = 0):
        # Reads input analog data from specified channel
        self.ai_device = self.daq_device.get_ai_device()
        self.ai_info = self.ai_device.get_info()
        number_of_channels = self.ai_info.get_num_chans_by_mode(AiInputMode.SINGLE_ENDED)
        if number_of_channels > 0:
            input_mode = AiInputMode.SINGLE_ENDED
        else:
            input_mode = AiInputMode.DIFFERENTIAL
        
        if channel > number_of_channels:
            channel = number_of_channels - 1
            
        ranges = self.ai_info.get_ranges(input_mode)
        
        data = self.ai_device.a_in(channel,input_mode,ranges[0],AInFlag.DEFAULT)
        return data
        
    def AOut(self, data, channel = 0):
        # Write output analog data to specified channel
        self.ao_device = self.daq_device.get_ao_device()
        self.ao_info = self.ao_device.get_info()
        output_range = self.ao_info.get_ranges()[0]
        self.ao_device.a_out(channel, output_range, AOutFlag.DEFAULT, data)
        
    def DOut(self, data, channel = 0):
        # Write output digital data to specified channel
        self.dio_device = self.daq_device.get_dio_device()
        
        # Get the port types for the device(AUXPORT, FIRSTPORTA, ...)
        self.dio_info = self.dio_device.get_info()
        port_types = self.dio_info.get_port_types()
        self.port_to_write = port_types[0]

        # Configure port
        self.dio_device.d_config_port(self.port_to_write, DigitalDirection.OUTPUT)

        # Writes output for bit
        self.dio_device.d_bit_out(self.port_to_write, channel, data)
    
    def AInScan(self, low_channel, high_channel, rate, samples_per_channel, scan_time = .25): 
        # Verify that the specified device supports hardware pacing for analog input.
        self.ai_device = self.daq_device.get_ai_device()
        self.ai_info = self.ai_device.get_info()
        if not self.ai_info.has_pacer():
            raise Exception('\nError: The specified DAQ device does not support hardware paced analog input')
        
        # Use the SINGLE_ENDED input mode to get the number of channels.
        # If the number of channels is greater than zero, then the device
        # supports the SINGLE_ENDED input mode; otherwise, the device only
        # supports the DIFFERENTIAL input mode.
        number_of_channels = self.ai_info.get_num_chans_by_mode(AiInputMode.SINGLE_ENDED)
        if number_of_channels > 0:
            input_mode = AiInputMode.SINGLE_ENDED
        else:
            input_mode = AiInputMode.DIFFERENTIAL
                
        # Verify the high channel does not exceed the number of channels, and
        # set the channel count.
        if high_channel >= number_of_channels:
            high_channel = number_of_channels - 1
        channel_count = high_channel - low_channel + 1
        
        # Get a list of supported analog input ranges.
        ranges = self.ai_info.get_ranges(input_mode)
                
        # Allocate a buffer to receive the data.
        data = create_float_buffer(channel_count, samples_per_channel)
        
        # Start the acquisition.
        rate = self.ai_device.a_in_scan(low_channel, high_channel, input_mode, ranges[0], samples_per_channel,
                                        rate, ScanOption.CONTINUOUS, AInScanFlag.DEFAULT, data)
        
        start_time = time.time()
        
        d = {}
        
        while (time.time() - start_time) <= scan_time:
            # Get the status of the background operation
            status, transfer_status = self.ai_device.get_scan_status()
            index = transfer_status.current_index

            # Display the data.
            for i in range(channel_count):
                d[i+low_channel] = data[index + i]
            sleep(0.1)          

        if self.daq_device:
            # Stop the acquisition if it is still running.
            if status == ScanStatus.RUNNING:
                self.ai_device.scan_stop()                
        
        return d
    
     
if __name__ == "__main__":
    daq = DAQ()
    daq.listDevices()
    daq.connect()
    data = daq.AIn(0)
    print(data)
    data = daq.AInScan(0,1,1000,10000,1)
    print(data)
    daq.DOut(1)
    daq.disconnect()
