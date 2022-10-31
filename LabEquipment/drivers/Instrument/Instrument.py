class Instrument(object):
    """Base class for pyvisa based instruments

    Encapsulates the pyvisa resource, and provides basic communications
    functions which can be used to implement instrument specific functions"""
    def __init__(self, resource):
        self.resource = resource

    def write(self, *args, **kwargs):
        """Writes a command string to the instrument"""
        return self.resource.write(*args, **kwargs)

    def read(self, *args, **kwargs):
        """Reads a string from the instrument"""
        return self.resource.read(*args, **kwargs)

    def query(self, *args, **kwargs):
        """Writes a command string to the instrument and reads the response"""
        return self.resource.query(*args, **kwargs)

    def idn(self):
        """Read the return value from the semi-standard "*IDN?" VISA command"""
        return self.query("*IDN?")
