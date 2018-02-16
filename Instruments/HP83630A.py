# HP83630A.py
#
# Paul Grimes, July 2014
#
# Module to operate the HP 83630A Synthesizer using PyVisa and GPIB.
#
import visa

class HP83630A(visa.GpibInstrument):
	'''Class for communicating with an HP 83630A Synthesizer'''
	def __init__(self, address="GPIB::19", strict=False):
		visa.GpibInstrument.__init__(self, address)
		# Check ID is correct
		self.idn = self.ask("*IDN?")
		if strict == True:
			if self.idn.split(",")[1] != "83630A":
				raise ValueError, "HP83630A Module: Specified instrument is not an HP 83630A"

	def getFreq(self):
		'''Return the current frequency of the synth'''
		freq = float(self.ask("FREQ?"))
		
		return freq
		
	def setFreq(self, freq):
		'''Set the frequency of the synth'''
		self.write("FREQ %.10G" % freq)
		
	def getAmp(self):
		'''Return the current amplitude of the synth in dBm'''
		amp = float(self.ask("POW?"))
		
		return amp
		
	def setAmp(self, amp):
		'''Set the amplitude of the synth in dBm'''
		self.write("POW %G" % amp)
		