# LabEquipment
Instrument Drivers and Applications using PyVisa, Measurement Computing's Universal Library, etc. to communicate with lab equipment and the Measurement Computing's USB DAQ hardware.

This code has been developed for use in the Smithsonian Astrophysical Observatory's Receiver Lab, and for use on Submillimeter Array.  Most of the code is of relevance to submillimeter and millimeter receiver testing.


# Installation
## Prerequisites
* Anaconda3 - after installation, it is recommended to set up an environment for installing and running this software
* MCC DAQ Drivers - required to run the MCC DAQ software, mostly in "mixers"
* NI VISA drivers or PyVisa Python VISA drivers - necessary to communicate with insruments over GPIB, Serial and Ethernet
* numpy, scipy, matplotlib, etc.

## Windows
* Install prerequisites
* Clone GitHub repository to computer
* Open Anaconda shell in appropriate environment (easiest way is with "play" button in "Environments" tab of Anaconda Navigator)
* Change to cloned repository directory
* Run "python setup.py install"
* !Run WIN-Install.bat! - !Does not work at present time!
