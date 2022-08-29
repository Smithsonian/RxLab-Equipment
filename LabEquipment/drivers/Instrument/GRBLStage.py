# MSL_XY.py
#
# Paul Grimes, Aug 2018
# from code by Larry Gardner, Jul 2018
#

from gerbil.gerbil import Gerbil

class GRBLStage(object):
    ''' Class for communicating with a GRBL based X-Y stage, using the Gerbil
    module.'''

    def __init__(self, serial_port, strict=False):
        self.resource = Gerbil()
        self.resource.cnect(serial_port)
        self.resource.poll_start()
        
    def set_vel_init(self, vel):
        'Set Initial Velocity'
        self.send_immediately("{} VI={:d}".format(drv, vel))

    def set_vel_max(self, vel):
        'Set max velocity'
        self.write("{} VM={:d}".format(drv, vel))

    def get_vel_init(self):
        'Returns Initial Velocity'
        return int(self.query("{} PR VI".format(drv)))

    def get_vel_max(self):
        'Returns Max Velocity'
        return int(self.query("{} PR VM".format(drv)))

    def get_vel(self):
        'Returns current velocity'
        return int(self.query("{} PR V".format(drv)))

    def set_accel(self, acl):
        'Sets acceleration'
        self.write("{} A={:d}".format(drv, acl))

    def set_decel(self, dec):
        'Sets deceleration'
        self.write("{} D={:d}".format(drv, dec))

    def get_accel(self):
        'Returns acceleration'
        return int(self.query("{} PR A".format(drv)))

    def get_params(self):
        'Returns all parameters'
        params = self.resource.request_settings()
        
        return params

    def move_abs(self, pos):
        'Moves to an absolute position from 0'
        self.resource.send_immediately("G90")
        self.resource.send_immediately("G1 X{pos[0]:.2f} Y{pos[1]:.2f}")

    def move_rel(self, pos):
        'Moves distance from current position'
        self.resource.send_immediately("G91")
        self.resource.send_immediately("G1 X{pos[0]:.2f} Y{pos[1]:.2f}")
        
    def set_zero(self):
        'Sets current position to the zero position'
        self.resource.send_immediately("G92 X0 Y0")
        
    def home(self):
        'Home the XY stage'
        self.resource.homing()

    def get_pos(self):
        'Returns position relative to 0'
        return int(self.query("{} PR P".format(drv)))

    def is_moving(self):
        return self.resource.cmode == "Run"

    def hold(self):
        'Holds instruction till motion has stopped'
        while self.is_moving():
            pass

    def zero(self):
        'Go to the zero position'
        self.resource.send_immediately("G1 X0 Y0")

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
    