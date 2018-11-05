# MSL.py
#
# Driver code from Newmark MDrive MSL linear slide
#
#  - Lawrence Gardner, Aug 2018
#  - Paul Grimes, Oct 2018
#


import Instrument

class MSL(Instrument.Instrument):
    ''' Class for communicating with a Newmark Systems MSL Linear Stage
        with MDrive Motor'''
    
    def __init__(self, resource, partyName=None, strict=False, softLimits=True):
        super().__init__(resource)
        
        self.resource.read_termination = '\r\n'
        
        if partyName == None:
            self.resource.write_termination = '\r' 
            self.prefix = ""
        else:
            self.resource.write_termination = '\n' 
            self.prefix = partyName + " "
        
        # Turns off echo for each command
        self.write("EM = 2")
        
        self.posLimit = None
        self.negLimit = None
        self.softLimits = softLimits
        
            
    def write(self, cmd):
        super().write(self.prefix+cmd)
        
    def query(self, cmd):
        return super().query(self.prefix+cmd)

    def setVelInit(self, vel):
        'Set Initial Velocity'
        self.write("VI=" +str(vel))
        
    def setVelMax(self, vel):
        'Set max velocity'
        self.write("VM="+str(vel))
    
    def getVelInit(self):
        'Returns Initial Velocity'
        self.VelInit = int(self.query("PR VI"))
        return self.VelInit
    
    def getVelMax(self):
        'Returns Max Velocity'
        self.VelMax = int(self.query("PR VM"))
        return self.VelMax
    
    def getVel(self):
        'Returns current velocity'
        self.velocity = int(self.query("PR V"))
        return self.velocity
    
    def setAccel(self, acl):
        'Sets acceleration'
        self.write("A="+str(acl))
    
    def setDecel(self, dec):
        'Sets deceleration'
        self.write("D="+str(dec))
        
    def getAccel(self):
        'Returns acceleration'
        self.accel = int(self.query("PR A"))
        return self.accel
        
    def getParam(self):
        'Returns all parameters'
        self.param = self.query("PR AL")
        return self.param
    
    def moveAbs(self, pos):
        """Moves to an absolute position from 0"""
        if self.softLimits:
            if self.posLimit:
                if self.posLimit < pos:
                    raise ValueError, "Requested position beyond positive range of motion of MSL {}".format(self.partyName)
            if self.negLimit:
                if self.negLimit > pos:
                    raise ValueError, "Requested position beyond negative range of motion of MSL {}".format(self.partyName)
        self.write("MA {:d}".format(pos))
    
    def moveRel(self, pos):
        """Moves distance from current position"""
        if self.softLimits:
            currPos = self.getPos()
            if self.posLimit:
                if self.posLimit < pos+currPos:
                    raise ValueError, "Requested position beyond positive range of motion of MSL {}".format(self.partyName)
            if self.negLimit:
                if self.negLimit > pos+currPos:
                    raise ValueError, "Requested position beyond negative range of motion of MSL {}".format(self.partyName)
        self.write("MR {:d}".format(pos))
    
    def setHome(self):
        """Sets current position to home (0 position)
        
        Also updates stored limits if any"""
        oldPos = self.getPos()
        self.write("P=0")
        if self.posLimit:
            self.posLimit = self.posLimit - oldPos
        if self.negLimit:
            self.negLimit = self.negLimit - oldPos

    def getPos(self):
        'Returns position relative to 0'
        self.position = int(self.query("PR P"))
        return self.position
            
    def isMoving(self):
        self.moving = self.query("PR MV")
        return self.moving
    
    def hold(self):
        'Holds instruction till motion has stopped'
        while self.isMoving() == '1':
            None
        
    def zero(self):
        'Makes the minimum position the home'
        self.moveAbs(-550000)
        self.hold()
        while self.getPos() != 0:
            self.setHome()
        
    def calibrate(self):
        'Calibration'
        self.write("SC")
        
    def findLimits(self):
        """Find the limits of travel of the stage, using the built in limit
        switches"""
        # Step forward until we run into the limit switch
        while not bool(int(self.query("PR I1"))):
            self.moveRel(1000)
        self.posLimit = self.getPos()
        
        # Step backward until we run into the limit switch
        while not bool(int(self.query("PR I2"))):
            self.moveRel(-1000)
        self.negLimit = self.getPos()
        
        
    def initialize(self):
        'Returns all variables to default'
        self.write("IP")
        self.read()
        'Turns off echo for each command'
        self.write("EM = 2")


if __name__ == "__main__":
    import visa
    
    # Run test code
    rm = visa.ResourceManager('@py')
    m = MSL(rm.open_resource("ASRL/dev/ttyUSB0", partyName="X"))
    print("Set up MSL Translation stage on {}".format(MSL.resource.resource_name)
    
    print("Current Position: {:d}".format(m.getPos()))

