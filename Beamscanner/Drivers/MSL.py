import Instrument

class MSL(Instrument.Instrument):
    ''' Class for communicating with a Newmark Systems MSL Linear Stage
        with MDrive Motor'''
    
    def __init__(self, resource, strict=False):
        
        super().__init__(resource)
        
        'Turns off echo for each command'
        self.write("EM = 2")
        self.resource.read_termination = '\r\n'
        self.resource.write_termination = '\r' 

    def setVelInit(self, vel):
        'Set Initial Velocity'
        self.write("VI=" +str(vel))
        
    def setVelMax(self, vel):
        'Set max velocity'
        self.write("VM="+str(vel))
    
    def getVelInit(self):
        'Returns Initial Velocity'
        self.VelInit = self.query("PR VI")
        return self.VelInit
    
    def getVelMax(self):
        'Returns Max Velocity'
        self.VelMax = self.query("PR VM")
        return self.VelMax
    
    def getVel(self):
        'Returns current velocity'
        self.velocity = self.query("PR V")
        return self.velocity
    
    def setAccel(self, acl):
        'Sets acceleration'
        self.write("A="+str(acl))
        
    def getAccel(self):
        'Returns acceleration'
        self.accel = self.query("PR A")
        return self.accel
        
    def getParam(self):
        'Returns all parameters'
        self.param = self.query("PR AL")
        return self.param
    
    def moveAbs(self, pos):
        'Moves to an absolute position from 0'
        self.write("MA " + str(pos))
    
    def moveRel(self, pos):
        'Moves distance from current position'
        self.write("MR " + str(pos))
    
    def setHome(self):
        'Sets current position to home (0 position)'
        self.write("P=0")

    def getPos(self):
        'Returns position relative to 0'
        self.position = self.query("PR P")
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
        self.setHome()
        
    def calibrate(self):
        'Calibration'
        self.write("SC")
        
    def initialize(self):
        'Returns all variables to default'
        self.write("IP")
        self.read()
        'Turns off echo for each command'
        self.write("EM = 2")
    