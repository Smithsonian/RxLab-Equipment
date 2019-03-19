#! loadVNAtoSKRF.py
#
# function to load data from Edward's VNA data format into
# a scikit-rf network

import skrf as rf
import numpy as np

def dBdeg_to_complex(dB, deg):
    """Return a complex NP array from a NP array in dB and deg"""
    return 10**(dB/20.)*np.exp(np.complex(0, 1)*np.deg2rad(deg))

def loadVNA_1port(filename):
    """Loads 1 port VNA data from filename and returns a skrf.Network representing the data"""
    data = np.loadtxt(filename)

    freq = rf.frequency.Frequency.from_f(data[:,0], unit="GHz")

    dB = data[:,1]
    deg = data[:,2]

    s11 = dBdeg_to_complex(dB, deg)

    # Convert 1d s11 array to skrf required 3d array
    s11 = np.reshape(s11, (s11.shape[0], 1, 1))

    net = rf.Network(f=freq.f_scaled, s=s11, z0=50, f_unit="GHz")

    return net
