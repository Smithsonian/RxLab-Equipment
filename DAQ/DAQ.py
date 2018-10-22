##################################################
#                                                #
# Wrapper around platform specific drivers 		 #
# for MCC DAQ devices                            #
#                                                #
# Paul Grimes, 2018                              #         
#                                                #
##################################################

import platform
if platform.system().lower().startsWith('win'):
	from DAQ_windows import *
else:
	from DAQ_linux import *
     
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
