# MSL_XY.py
#
# Paul Grimes, Aug 2018
# from code by Larry Gardner, Jul 2018
#
import time

import numpy as np

from gerbil.gerbil import Gerbil

class GRBLStage(object):
    ''' Class for communicating with a GRBL based X-Y stage, using the Gerbil
    module.'''

    def __init__(self, serial_port, strict=False):
        self.resource = Gerbil()
        self.resource.cnect(serial_port)
        self.resource.poll_start()
        
        self.feedrate = 3000
        
        
    def get_max_pos(self, axis=None):
        """Retrun the maximum travel in mm.
        
        arguments:
            axis (int): axis to set maximum travel for. One of 0 (x), 1 (y), 2(z)
        returns:
            float or numpy.array: maximum limits in mm.
        """
        if axis:
            return self.resource.settings[str(130+axis)]
        else:  # Get the limits for all axes
            return np.array([self.resource.settings[str(130)], self.resource.settings[str(131), self.resource.settings[str(132)]]])
    
    def set_max_pos(self, maxpos, axis):
        """Set the maximum travel in mm.
        
        arguments:
            maxpos (float): maximum travel in mm.
            axis (int): axis to set maximum travel for. One of 0 (x), 1 (y), 2(z)
        """
        self.resource.send_immediately(f"${130+axis:d}={maxpos:.2f}")
        self.resource.request_settings()
        
    def set_vel(self, vel):
        'Set default speed in mm/min'
        self.feedrate = vel

    def get_vel_max(self, axis=None):
        """Retrun the maximum velocity in mm/min.
        
        arguments:
            axis (int): axis to set maximum travel for. One of 0 (x), 1 (y), 2(z)
        returns:
            float or numpy.array: maximum velocity in mm/min.
        """
        if axis:
            return self.resource.settings[str(110+axis)]
        else:  # Get the limits for all axes
            return np.array([self.resource.settings[str(110)], self.resource.settings[str(111), self.resource.settings[str(112)]]])

    def set_vel_max(self, maxvel, axis=0):
        'Set Max Velocity (for axis 0 = x, which will be the same as y by default'
        self.resource.send_immediately(f"${str(110+axis):d}={maxvel:.2f}"]
        self.resource.request_settings()

    def get_vel(self):
        'Returns current velocity'
        return self.feedrate

    def get_accel(self, axis=None):
        """Retrun the acceleration in mm/s^2.
        
        arguments:
            axis (int): axis to set maximum travel for. One of 0 (x), 1 (y), 2(z)
        returns:
            float or numpy.array: acceleration in mm/s^2.
        """
        if axis:
            return self.resource.settings[str(120+axis)]
        else:  # Get the limits for all axes
            return np.array([self.resource.settings[str(120)], self.resource.settings[str(121), self.resource.settings[str(122)]]])
        
    def set_vel_max(self, acc, axis=0):
        'Set acceleration for axis in mm/s^2'
        self.resource.send_immediately(f"${str(120+axis):d}={acc:.2f}")
        self.resource.request_settings()

    def get_params(self):
        'Returns all parameters as a dictionary of GRBL $ values'
        return self.resource.settings

    def move_abs(self, pos, feedrate=self.feedrate, blocking=True):
        'Moves to an absolute position from 0'
        self.resource.send_immediately("G90")
        self.resource.send_immediately(f"G1 X{pos[0]:.2f} Y{pos[1]:.2f} F{feedrate:.2f}")
        
        if blocking:
            self.block_while_moving()

    def move_rel(self, pos, feedrate=self.feedrate, blocking=True):
        'Moves distance from current position'
        self.resource.send_immediately("G91")
        self.resource.send_immediately(f"G1 X{pos[0]:.2f} Y{pos[1]:.2f} F{feedrate:.2f}")
                
        if blocking:
            self.block_while_moving()
        
    def set_zero(self):
        'Sets current position to the zero position'
        self.set_curr_pos([0, 0])
        
    def set_curr_pos(self, pos):
        'Sets the current position to an (X, Y) value, defining a new origin for the XY coordinate system'
        self.resource.send_immediately(f"G92 X{pos[0]:.2f} Y{pos[1]:.2f}")
        # Update hash state so that get_pos returns the correct position
        self.resource.get_hash_state()
        
    def home(self, blocking=True):
        'Home the XY stage'
        self.resource.homing()
        if blocking:
            self.block_while_moving()

    def get_pos(self):
        'Returns position relative to the current G92 origin'
        return np.array(self.resource.cmpos) - np.array(self.resource.settings_hash["G92"])
    
    def get_abs_pos(self):
        'Returns the absolute position in machine coordinates'
        return np.array(self.resource.cmpos)

    def is_moving(self):
        return self.resource.cmode == "Run"

    def block_while_moving(self):
        'Holds instruction till motion has stopped'
        time.sleep(self.resource.polling_interval)
        while self.is_moving():
            time.sleep(self.resource.polling_interval)

    def zero(self, blocking=True):
        'Go to the zero position'
        self.resource.send_immediately("G1 X0 Y0")
        if blocking:
            self.block_while_moving()

    def initialize(self):
        'Reset the GRBL controller'
        self.resource.reset()

if __name__ == "__main__":
    # Run test code
    m = XY_Stage("/dev/ttyUSB0")
    print("Set up communication with MSL Translation stages on {}".format(m.resource))
    print()
    print("Current Position of Stage: {:d} {:d}".format(m.get_pos()))
    print()
    print("Parameters of Stage:")
    params = m.get_params(m.X)
    for p in params:
        print("\t{}".format(p))
    