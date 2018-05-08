# Instrument.py
#
# Paul Grimes, Feb 2018
#
# A base class for building instrument drivers based on PyVISA.  We subclass this to
# make specific drivers for instruments
#
#

class Instrument(object):
    '''Class for communicating with a PyVisa Instrument

    This class, and drivers based on it are instantiated by passing a PyVISA resource created
    by the visa resource manager.  e.g.:

    import visa
    rm = visa.ResourceManager()
    inst = Instrument(rm.open_resource('GPIB::8'))'''

    def __init__(self, resource, strict=False, idString=None):
        self.resource = resource

        # Check ID is correct
        if strict == True and idString:
            if self.idn.split(",")[1] != idString:
                raise ValueError("Instrument ID is not {:s}: got {:s}".format(idString, self.idn))

    def write(self, *args, **kwargs):
        return self.resource.write(*args, **kwargs)

    def read(self, *args, **kwargs):
        return self.resource.read(*args, **kwargs)

    def query(self, *args, **kwargs):
        return self.resource.query(*args, **kwargs)

    @property
    def idn(self):
        return self.query("*IDN?")
