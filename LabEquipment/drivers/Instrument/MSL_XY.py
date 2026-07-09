# MSL_XY.py
#
# Paul Grimes, Aug 2018
# from code by Larry Gardner, Jul 2018
#
import time
from collections.abc import Iterable

from ..Instrument import Instrument

class MSL_XY(Instrument.Instrument):
    ''' Class for communicating with two Newmark Systems MSL Linear Stages
        with MDrive Motors, set up as an X/Y scanner on a single IEEE-485 bus.

        MDrive Motors must have been configured to Party Mode, with
        device names X and Y, with command echo turned off

        Commands can be sent to either or both drives using drv keywords,
        where drv is either device name or "*" for both devices.

        Default device names for the X and Y drives are built into the
        object as msl.X and msl.Y'''

    def __init__(self, resource, strict=False):

        super().__init__(resource)
        
        self.resource.baud_rate = 9600
        
        self.resource.encoding = 'windows-1252'

        self.resource.read_termination = '\r\n'
        self.resource.write_termination = '\n'

        self.X = "X"
        self.Y = "Y"

    def set_vel_init(self, vel):
        'Set initial velocity for both drives'
        
        if not isinstance(vel, Iterable):
            vel = [vel, vel]
            
        self.set_vel_init_drv(int(vel[0]), self.X)
        self.set_vel_init_drv(int(vel[1]), self.Y)

    def set_vel_init_drv(self, vel, drv="*"):
        'Set Initial Velocity'
        self.write("{} VI={:d}".format(drv, vel))

    def set_vel(self, vel):
        self.set_vel_max(vel)

    def set_vel_max(self, vel):
        'Set the max velocity for each drive'
        if not isinstance(vel, Iterable):
            vel = [vel, vel]
        
        self.set_vel_max_drv(int(vel[0]), self.X)
        self.set_vel_max_drv(int(vel[1]), self.Y)

    def set_vel_max_drv(self, vel, drv="*"):
        'Set max velocity'
        self.write("{} VM={:d}".format(drv, vel))

    def get_vel_init(self):
        'return initial velocity for each drive'
        return self.get_vel_init_drv(self.X), self.get_vel_init_drv(self.Y)

    def get_vel_init_drv(self, drv="*"):
        'Returns Initial Velocity'
        return int(self.query("{} PR VI".format(drv)))

    def get_vel_max(self):
        'Return max velocity for each drive'
        return self.get_vel_max_drv(self.X), self.get_vel_max_drv(self.Y)

    def get_vel_max_drv(self, drv="*"):
        'Returns Max Velocity'
        return int(self.query("{} PR VM".format(drv)))

    def get_vel(self):
        'Get the velocity of each drive'
        return self.get_vel_drv(self.X), self.get_vel_drv(self.Y)

    def get_vel_drv(self, drv="*"):
        'Returns current velocity'
        return int(self.query("{} PR V".format(drv)))

    def set_accel(self, acl):
        if not isinstance(acl, Iterable):
            acl = [acl, acl]
        
        'Set acceleration for both drives'
        self.set_accel_drv(int(acl[0]), self.X)
        self.set_accel_drv(int(acl[1]), self.Y)

    def set_accel_drv(self, acl, drv="*"):
        'Sets acceleration'
        self.write("{} A={:d}".format(drv, acl))

    def set_decel(self, dec):
        'Set deceleration for both drives'
        if not isinstance(dec, Iterable):
            dec = [dec, dec]
        
        self.set_decel_drv(int(dec[0]), self.X)
        self.set_decel_drv(int(dec[1]), self.Y)

    def set_decel_drv(self, dec, drv="*"):
        'Sets deceleration'
        self.write("{} D={:d}".format(drv, dec))

    def get_accel(self):
        'Return accelerations from both drives'
        return self.get_accel_drv(self.X), self.get_accel_drv(self.Y)

    def get_accel_drv(self, drv="*"):
        'Returns acceleration'
        return int(self.query("{} PR A".format(drv)))

    def get_params(self):
        'Return all parameters from both drives'
        return self.get_params_drv(self.X), self.get_params_drv(self.Y)

    def get_params_drv(self, drv="*"):
        'Returns all parameters'
        self.write("{} PR AL".format(drv))
        params = []
        while True:
            rd = self.read()
            if rd=="":
                break
            else:
                params.append(rd)
        return params

    def move_abs(self, position, blocking=True):
        """Move both stages to position
        
        Arguments:
            position (tuple of ints)
        """
        if isinstance(position, Iterable):
            self.move_abs_drv(int(position[0]), self.X)
            self.move_abs_drv(int(position[1]), self.Y)
        else:
            self.move_abs_drv(int(position), self.X)
            
        if blocking:
            self.block_while_moving()

    def move_abs_drv(self, pos, drv="*"):
        'Moves to an absolute position from 0'
        self.write("{} MA {:d}".format(drv, pos))

    def move_rel(self, distance, blocking=True):
        'Move both stages by a distance'
        if not isinstance(distance, Iterable):
            distance = [distance, 0]
    
        self.move_rel_drv(int(distance[0]), self.X)
        self.move_rel_drv(int(distance[1]), self.Y)
        
        if blocking:
            self.block_while_moving()

    def move_rel_drv(self, dis, drv="*"):
        'Moves distance from current position'
        self.write("{} MR {:d}".format(drv, dis))

    def set_zero(self):
        'Sets current position to zero (0 position)'
        self.write("X P=0")
        self.write("Y P=0")
        
    def set_zero_drv(self, drv="*"):
        self.write(f"{drv} P=0")
        
    def set_curr_pos(self, position):
        """Set the current position
        
        Arguments:
            position (tuple of ints): tuple of current x and y positions to set"""
        if not isinstance(position, Iterable):
            position = [position, position]
            
        self.set_curr_pos_drv(int(position[0]), self.X)
        self.set_curr_pos_drv(int(position[1]), self.Y)
        
    def set_curr_pos_drv(self, position, drv="*"):
        'Set the current position for one drive'
        self.write(f"{drv} P={position:d}")
        
    def get_pos(self):
        'Returns position relative to 0'
        return self.get_pos_drv(self.X), self.get_pos_drv(self.Y)

    def get_pos_drv(self, drv="*"):
        'Returns position relative to 0 for one stage'
        return int(self.query("{} PR P".format(drv)))

    def is_moving(self):
        return self.is_moving_drv(self.X) or self.is_moving_drv(self.Y)

    def is_moving_drv(self, drv="*"):
        return bool(int(self.query("{} PR MV".format(drv))))

    def block_while_moving(self):
        'Block while either drive is moving'
        self.block_while_moving_drv(self.X)
        self.block_while_moving_drv(self.Y)

    def block_while_moving_drv(self, drv="*"):
        'Holds instruction till motion has stopped'
        while self.is_moving_drv(drv):
            time.sleep(0.05)

    def home(self):
        """Home both stages"""
        self.home_drv(self.X)
        self.home_drv(self.Y)

    def home_drv(self, drv="*"):
        'Makes the minimum position the home'
        self.move_abs_drv(-550000, drv)
        self.block_while_moving_drv(drv)
        
        self.set_zero_drv(drv)

    def zero(self, blocking=True):
        'Return the stage to the current zero position'
        self.zero_drv(self.X)
        self.zero_drv(self.Y)
        
        if blocking:
            self.block_while_moving()
        
    def zero_drv(self, drv="*"):
        'Return a stage to the current zero position'
        self.move_abs_drv(0, self.X)
        self.move_abs_drv(0, self.Y)

    def calibrate(self):
        'Calibrate both drives'
        self.calibrate_drv(self.X)
        self.calibrate_drv(self.Y)

    def calibrate_drv(self, drv="*"):
        'Calibration'
        self.write("{} SC".format(drv))

    def initialize(self):
        'Initialize both drives'
        self.initialize_drv(self.X)
        self.initialize_drv(self.Y)

    def initialize_drv(self, drv="*"):
        'Returns all variables to values stored in NVM'
        self.write("{} IP".format(drv))

if __name__ == "__main__":
    import pyvisa

    # Run test code
    rm = pyvisa.ResourceManager('@py')
    m = MSL_XY(rm.open_resource("ASRL/dev/ttyUSB0"))
    print("Set up communication with MSL Translation stages on {}".format(m.resource.resource_name))
    print()
    print("Current Position of X drive: {:d}".format(m.getPos(m.X)))
    print("Current Position of Y drive: {:d}".format(m.getPos(m.Y)))
    print()
    print("Parameters of X drive:")
    params = m.getParams(m.X)
    for p in params:
        print("\t{}".format(p))
    print()
    print("Parameters of Y drive:")
    params = m.getParams(m.Y)
    for p in params:
        print("\t{}".format(p))
