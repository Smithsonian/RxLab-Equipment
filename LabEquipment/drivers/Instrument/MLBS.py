import socket

class MLBS(object):
    """Class for operating the Micro Lambda Wireless MLBS series of
    benchtop YIG synthesizers, using UDP sockets over ethernet"""
    def __init__(self, ip_address, port=30303):
        self._ip_address = ip_address
        self._port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)

        # Get some initial data
        self._fmax = self.getFMax()
        self._fmin = self.getFMin()
        self._freq = self.getFreq()
        self._levelcontrol = self.getLevelControl()
        if self._levelcontrol:
            self._pmax = self.getPMax()
            self._pmin = self.getPMin()
            self._power = self.getPower()
        else:
            self._pmax = None
            self._pmin = None
            self._power = None
        self._model = self.getModel()
        self._serial = self.getSerial()

    def read(self, bytesize=1024):
        """Listen for <bytesize> bytes from UDP client"""
        data, addr = self.sock.recvfrom(bytesize)
        if data:
            # decode to a string and remove extraneous stuff
            data = data.decode("utf-8").strip().split("\x00")[0]
        return data

    def write(self, message):
        """Write message to UDP client"""
        self.sock.sendto(bytes(message, "UTF-8"), (self.ip_address, self.port))

    @property
    def ip_address(self):
        """The IP address of the YIG filter"""
        return self._ip_address

    @ip_address.setter
    def ip_address(self, ip):
        """Set the IP address. Since this likely changes the instrument,
        we need to get all new data about the instrument"""
        self.__init__(ip, port=self._port)

    @property
    def port(self):
        """The port of the instrument"""
        return self._port

    @port.setter
    def port(self, p):
        """Set the port.

        Communication probably didn't work before this was set, but we
        have lazy checking of the values, so we'll rely on that."""
        self._port = p

    @property
    def freq(self):
        """The current frequency of the synthesizer"""
        try:
            freq = self._freq
        except AttributeError:
            self._freq = self.getFreq()
            freq = self._freq
        return freq

    @freq.setter
    def freq(self, freq):
        self.setFreq(freq)

    @property
    def fmin(self):
        """The minimum frequency of the YIG filter.  This can't change
        so we only read it the first time"""
        try:
            freqmin = self._fmin
        except AttributeError:
            self._fmin = self.getFMin()
            freqmin = self._fmin
        return freqmin

    @property
    def fmax(self):
        """The maximum frequency of the YIG filter.  This can't change
        so we only read it the first time"""
        try:
            freqmax = self._fmax
        except AttributeError:
            self._fmax = self.getFMax()
            freqmax = self._fmax
        return freqmax
    
    @property
    def power(self):
        """The current frequency of the synthesizer"""
        try:
            power = self._power
        except AttributeError:
            self.getPower()
            power = self._power
        return power
    
    @power.setter
    def power(self, power):
        self.setPower(power)
    
    @property
    def pmin(self):
        """The minimum power output of the synthesizer.  This can't change
        so we only read it the first time"""
        try:
            powermin = self._pmin
        except AttributeError:
            self._pmin = self.getPMin()
            powermin = self._pmin
        return powermin

    @property
    def pmax(self):
        """The minimum power output of the synthesizer.  This can't change
        so we only read it the first time"""
        try:
            powermax = self._pmax
        except AttributeError:
            self._pmax = self.getPMax()
            powermax = self._pmax
        return powermax

    @property
    def model(self):
        """The model number of the YIG filter.  This can't change so we
        only read it the first time"""
        try:
            mod = self._model
        except AttributeError:
            self._model = self.getModel()
            mod = self._model
        return mod

    @property
    def serial(self):
        """The serial number of the YIG filter.  This can't changes so we
        only read it the first time"""
        try:
            ser = self._serial
        except AttributeError:
            self._serial = self.getSerial()
            ser = self._serial
        return ser


    def getFMin(self):
        """Get the minimum frequency setting in MHz"""
        self.write("R0003")
        f = self.read()
        return float(f)

    def getFMax(self):
        """Get the maximum frequency setting in MHz"""
        self.write("R0004")
        f = self.read()
        return float(f)

    def getFreq(self):
        """Get the current frequency setting in MHz"""
        self.write("R0016")
        self._freq = float(self.read())
        return self.freq

    def setFreq(self, freq):
        """Set the frequency in MHz"""
        if freq > self.fmax:
            raise ValueError("MLBS: Requested frequency of {:f} MHz too high".format(freq))
        if freq < self.fmin:
            raise ValueError("MLBS: Requested frequency of {:f} MHz too low".format(freq))
        self.write("F{:.3f}".format(freq))
        self._freq = self.getFreq()

    def getLevelControl(self):
        """Determine whether power control is installed"""
        self.write("R0043")
        l = self.read()
        if l=="Yes":
            return True
        else:
            return False

    def getPMax(self):
        """Get the maximum power level in dBm"""
        if self._levelcontrol:
            self.write("R0044")
            power = self.read()
            return float(power)
        else:
            return None
        
    def getPMin(self):
        """Get the minimum power level in dBm"""
        if self._levelcontrol:
            self.write("R0045")
            power = self.read()
            return float(power)
        else:
            return None

    def getPower(self):
        """Get the current power level in dBm"""
        if self._levelcontrol:
            self.write("R0048")
            self._power = float(self.read())
            return self.power
        else:
            return None

    def setPower(self, power):
        """Set the frequency in MHz"""
        if self._levelcontrol:
            if power > self.pmax:
                raise ValueError("MLBS: Requested level of {:f} dBm too high".format(power))
            if power < self.pmin:
                raise ValueError("MLBS: Requested level of {:f} dBm too low".format(power))
            self.write("L{:.3f}".format(power))
            self.getPower()
        else:
            raise RuntimeWarning("MLBS does not have level control installed")

    def getModel(self):
        """Get the Model Number"""
        self.write("R0000")
        return self.read()

    def getSerial(self):
        """Get the serial number"""
        self.write("R0001")
        return self.read()
