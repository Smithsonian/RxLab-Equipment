# HP83630A.py
#
# Paul Grimes, July 2014
#
# Module to operate the HP 83630A Synthesizer using PyVisa and GPIB.
#
import visa

class HP83630A(object):
	'''Class for communicating with an HP 83630A Synthesizer'''
	def __init__(self, InstAddr="GPIB::19", strict=False):
  		"""Create Synthesizer object.

		InstAddr is the PyVisa address of the Synthesizer - try "GPIB::19" by default in the lab"""
  		self.rm = visa.resource_manager()
  		self.inst = self.rm.get_resource(InstAddr)
		# Check ID is correct
		self.idn = self.inst.query("*IDN?")
		if strict == True:
			if self.idn.split(",")[1] != "83630A":
				raise ValueError, "HP83630A Module: Specified instrument is not an HP 83630A"

	def getFreq(self):
		'''Return the current frequency of the synth'''
		freq = float(self.inst.query("FREQ?"))

		return freq

	def setFreq(self, freq):
		'''Set the frequency of the synth'''
		self.inst.query("FREQ {.10g}".format(freq))

	def getAmp(self):
		'''Return the current amplitude of the synth in dBm'''
		amp = float(self.inst.query("POW?"))

		return amp

	def setAmp(self, amp):
		'''Set the amplitude of the synth in dBm'''
		self.inst.query("POW {:g}".format(amp))

	def setExtRefAuto(self):
		'''Set the synth to use the external 10 MHz reference'''
		# TODO: Replace with correct command
		#self.inst.write("ROSC:SOUR:AUTO")
		pass

	def getExtRef(self):
		'''Get the reference source in use by the synth'''
		# TODO: Replace with correct command
		#refSource = self.inst.query("ROSC:SOUR?")
		#return refSource
		pass

	def getRFOutput(self):
		'''Return the RF Output State as either On (1) or Off (0)'''
		# TODO: Replace with correct command
		#rfOn = self.inst.query("OUTP:STAT?")
		#return int(rfOn)
		pass

	def setRFOutput(self, state):
		'''Set the RF Output to either On (1) of Off (0)'''
		# TODO: Replace with correct command
		#self.inst.write("OUTP:STAT {:b}".format(state))
		pass
