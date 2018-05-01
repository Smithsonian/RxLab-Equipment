# HP 8562A Spectrum Analyzer operation code
# Paul Grimes, March 2016

import pyvisa

class SpecA:
  def __init__(self, InstAddr="GPIB::2"):
    """Create Spectrum Analyzer object.
  
      InstAddr is the address of the spectrum analyzer - try "GPIB::2" by default"""
    
    self.rm = pyvisa.resource_manager()
    self.speca = self.rm.get_resource(InstAddr)
    self.speca.query("INI?")
    
    # Get initial frequency sweep data
    self.get_freq_span()
    self.get_freq_center()
    self.get_freq_start()
    self.get_freq_stop()
    self.get_freq_step()
    self.rbw = get_rbw()
    self.vbw = get_vbw()
    
    self.sweep_run = False
    
  def visa_cmd(self, cmd):
    """Pass VISA command through to instrument
    
    No checking is done"""
    self.speca.write(cmd)
    
    
  def visa_query(self, cmd):
    """Pass VISA query through to instrument and return result
    
    No checking is done"""
    return self.speca.query(cmd)
    
    
  def set_freq_span(self, span):
    """Set frequency span to <span> GHz"""
    self.speca.write("SP " + str(span*1000.0) + "MHZ")
    
    # Get new frequency sweep data
    self.get_freq_span()
    self.get_freq_center()
    self.get_freq_start()
    self.get_freq_stop()
    self.get_freq_step()
    
    self.sweep_run = False
    
  def get_freq_span(self):
    """Read the frequency span from the Spectrum Analyzer"""
    self.freq_span = self.query_values("SP?")[0]/1.0e9
    return freq_span
    
    
  def set_freq_center(self, cfreq):
    """Set center frequency to <cfreq> GHz"""
    self.speca.write("CF " + str(cfreq*1000.0) + "MHZ")
    
    self.get_freq_span()
    self.get_freq_center()
    self.get_freq_start()
    self.get_freq_stop()
    self.get_freq_step()
    
    self.sweep_run = False
    
  def get_freq_center(self):
    """Read the frequency center from the Spectrum Analyzer"""
    self.freq_center = self.query_values("CF?")[0]/1.0e9
    return self.freq_center  
    
  def set_freq_start(self, start):
    """Set start frequency to <start> GHz"""
    self.speca.write("FA " + str(start*1000.0) + "MHZ")
    
    # Get new frequency sweep data
    self.get_freq_span()
    self.get_freq_center()
    self.get_freq_start()
    self.get_freq_stop()
    self.get_freq_step()
    
    self.sweep_run = False
    
  def get_freq_start(self):
    """Read the frequency center from the Spectrum Analyzer"""
    self.freq_start = self.query_values("FA?")[0]/1.0e9
    return self.freq_start    

  def set_freq_stop(self, stop):
    """Set start frequency to <stop> GHz"""
    self.speca.write("FB " + str(stop*1000.0) + "MHZ")
    
    # Get new frequency sweep data
    self.get_freq_span()
    self.get_freq_center()
    self.get_freq_start()
    self.get_freq_stop()
    self.get_freq_step()
    
    self.sweep_run = False
        
  def get_freq_stop(self):
    """Read the frequency center from the Spectrum Analyzer"""
    self.freq_stop = self.query_values("FB?")[0]/1.0e9
    
    return self.freq_stop
    
  def get_freq_step(self):
    """Calculate the frequency step in the trace.
    
    The HP8562A uses 601 data points per trace."""
    self.freq_step = (self.freq_stop-self.freq_start)/600.
    
    return self.freq_step
    

  def set_rbw(self, rbw):
    """Set resolution bandwidth in Hz
    
    Resolution bandwidth should be 1 or 3 times power of 10 in 
    range (10Hz - 3MHz).  If other value is passed, valid value above
    requested value will be set. 
    (i.e. 101kHz become 300kHz, 99kHz becomes 100kHz)"""
    self.speca.write("RB " + str(rbw) + "HZ")
    
    self.rbw = self.get_rbw()
    
    self.sweep_run = False

  def get_rbw(self):
    """Return the current resolution bandwidth in Hz"""
    self.rbw = self.speca.query_for_values("RB?")[0]
    return self.rbw
    

  def set_vbw(self, vbw):
    """Set video bandwidth in Hz
    
    Video bandwidth should be 1 or 3 times power of 10 in 
    range (1Hz - 3MHz).  If other value is passed, valid value above
    requested value will be set. 
    (i.e. 101kHz become 300kHz, 99kHz becomes 100kHz)"""
    self.speca.write("VB " + str(vbw) + "HZ")
    
    self.vbw = self.get_vbw()
    
    self.sweep_run = False
  
  def get_vbw(self):
    """Return the current resolution bandwidth in Hz"""
    self.vbw = self.speca.query_for_values("VB?")[0]
    return self.vbw
    
    
  def sweep(self, wait=True):
    """Runs a single sweep and waits until complete if wait==True"""
    self.speca.write("TS")
    
    self.sweep_run = False
    
    if wait:
        while self.sweep_run == False:
            time.sleep(1.0)
            if self.speca.query("DONE?") == "1":
                break
                  
    self.sweep_run = True
    return self.sweep_run
  
  def get_trace(self):
    """Return whole trace as [freq, amplitude] pairs"""
    if self.sweep_run == False:
      print "Sweep not run - running now"
      self.sweep()
    
    # Set the trace data format to real ASCII numbers
    self.speca.write("TDF P")
    
    # Get the format of the data
    self.log = self.speca.query("LG?")
    self.aunit = self.speca.query("AUNIT?")
    self.refLevel = self.speca.query_for_values("RL?")[0]
    
    
    # Get trace data from instrument
    # this is in units of 0.01 dBm
    trace_data = self.speca.query_values("TRA?")
    
    data = []
    for f in range(601):
      data.append([(self.freq_start + f*self.freq_step), trace_data[f]])
      
    self.trace = data
    
    return self.trace
    
      
# Function to aid in saving trace data to a file  
def save_trace_to_csv(trace_data, filename, comment="Spectrum analyzer data"):
  """Save trace data to csv file"""
  
  header = """
  # {}
  #
  # Frequency Range {} - {}
  # Resolution Bandwidth {}
  # Video Bandwidth {}
  # Amplitude Units {} {}
  # Ref Level {}
  #
  # Freq     Amp
  """.format(comment, self.freq_start, self.freq_stop, self.rbw, self.vbw, self.log, self.aunit, self.refLevel)
  
  file = open(filename, "w")
  
  file.write(header+"\n\r")
  
  for p in trace_data:
    line = str(p[0]) + ", " + str(p[1]) + "\n"
    file.write(line)
    
  file.close()
