# AgilentE8257D.py
#
# Paul Grimes, July 2014
#
# Module to operate the Agilent E8257D Synthesizer using PyVisa and GPIB.
#
import visa

class AgilentE8257D(visa.GpibInstrument):
	'''Class for communicating with an Agilent E8257D Synthesizer'''
	def __init__(self, address="GPIB::18", strict=False):
		visa.GpibInstrument.__init__(self, address)
		# Check ID is correct
		self.idn = self.ask("*IDN?")
		if strict == True:
			if self.idn.split(",")[1] != " E8257D":
				raise ValueError, "AgilentE8257D Module: Specified instrument is not an Agilent E8257D"

	def getFreq(self):
		'''Return the current frequency of the synth'''
		freq = float(self.ask("FREQ?"))
		
		return freq
		
	def setFreq(self, freq):
		'''Set the frequency of the synth'''
		self.write("FREQ %.10G" % freq)
		
	def getAmp(self):
		'''Return the current amplitude of the synth in dBm'''
		amp = float(self.ask("SOUR:POW?"))
		
		return amp
		
	def setAmp(self, amp):
		'''Set the amplitude of the synth in dBm'''
		self.write("SOUR:POW %G" % amp)
		
	def setExtRefAuto(self):
		'''Set the synth to use the external 10 MHz reference'''
		self.write("ROSC:SOUR:AUTO")
		
	def getExtRef(self):
		'''Get the reference source in use by the synth'''
		refSource = self.ask("ROSC:SOUR?")
		
		return refSource
		
	def getRFOutput(self):
		'''Return the RF Output State as either On (1) or Off (0)'''
		rfOn = self.ask("OUTP:STAT?")
		
		return int(rfOn)
		
	def setRFOutput(self, state):
		'''Set the RF Output to either On (1) of Off (0)'''
		self.write("OUTP:STAT %d" % state)
