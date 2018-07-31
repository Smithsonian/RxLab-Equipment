class Instrument(object):
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
    
    def idn(self):
        return self.query("*IDN?")
