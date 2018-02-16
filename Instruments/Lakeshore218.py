# Lakeshore 218 Temperature Monitor module
# Paul Grimes, Sept. 2008

import pyvisa
import string

class Lakeshore:
  def __init__(self, InstAddr="GPIB::11"):
    """Create Lakeshore Temperature Monitor object.
  
      InstAddr is the address of the Temperature Monitor - try "GPIB::11" by default"""
    
	rm = pyvisa.ResourceManager()
	
    if InstAddr[0:3] == "COM": # We are using RS232 and need to set up the instrument more carefully
        self.lakeshore = rm.open_resource(InstAddr, baud_rate=9600, data_bits=7, stop_bits=1, parity=visa.odd_parity, term_chars="\r\n", delay = 0.05)
    else:  # We are probably using GPIB, but don't really know.
        self.lakeshore = rm.open_resource(InstAddr)
    

  # Basic generic Visa commands    
  def visa_cmd(self, cmd):
    """Pass VISA command through to instrument
    
    No checking is done"""
    self.lakeshore.write(cmd)
    
    
  def visa_query(self, cmd):
    """Pass VISA query through to instrument and return result as a single string.
    
    No checking is done"""
    return self.lakeshore.query(cmd)
	
  def visa_query_values(self, cmd):
    """Pass the VISA query through and get list of values in return
	
	No checking is done"""
	return self.lakeshore.query_ascii_values(cmd)
	
  ### Device specific Visa commands that wrap around the above generic commands
  def get_temp_log(self,outfilename,sensor_list):
    """ Get an entire temperature log off the lakeshore: 
    Takes output text filename and  python list of sensors to read from
    Dumps output (in ohms, Kelvin or whatever) into a space seperated 
    text file"""
    
    
    last_log=int(self.visa_query("LOGNUM?"))
    print "Last log was %i " % last_log
    
    f=open(outfilename,'w')
    
    for i in range(1,last_log+1):
        print "fetching record %i" % i
        output_string=""
        log_str=self.visa_query("LOGVIEW? %i 1" % (i,j))
        log_list=log_str.split(",")
        output_string += (log_list[0]+" "+log_list[1])
        for j in sensor_list:
          log_str=self.visa_query("LOGVIEW? %i %i" % (i,j))
          log_list=log_str.split(",")
          output_string +=(log_list[2]+" ")
        
        
        f.write(output_string+"\n")
        print output_string 
    f.close
    print "...done"
    
    
  def get_log(self):
    """Read the logged data to a python list of readings.
    This functions checks to see which sensors are active, and which
    units are in use.
    This header data is included in position 0 of the list of readings,
    and should be treated as a file header"""
    
    # Get number of log readings per record
    readings = self.get_logreadings()
    
    # Get number of log records
    records = self.get_lognum()
    
    # Set up the header, getting the input and units for each log record
    logsetup = []
    for i in range(1, readings+1):
        logsetup.append([self.get_loginput(i), self.get_logunits(i)])
    
    logheader = ["# Date,Time"]
    
    for r in logsetup:
        logheader.append("T%d (%s)" % (r[0], r[1]))
    
    
    # Start reading the log
    log = [logheader]
    
    for record in range(1, records+1):
        logrecord = [self.get_logdatetime(record)]
        for reading in range(1, readings+1):
            logrecord.append(self.get_logvalue(record, reading))
            
        log.append(logrecord)
        
    return log
    
    
  def get_logvalue(self, record, reading):
    """Returns a single reading from a record in the log"""
    retval = self.visa_query("LOGVIEW? %d %d" % (record, reading))
    
    return string.atof(retval.split(",")[2])
    
    
  def get_logdatetime(self, record):
    """Return the date and time that a log record was recorded"""
    retval = self.visa_query("LOGVIEW? %d %d" % (record, 1))
    
    datetime = retval.split(",")[0:2]
    
    return string.join(datetime, ",")
    
    
  def get_lognum(self):
    """Returns the number of records in the log"""
    
    return string.atoi(self.visa_query("LOGNUM?"))
    
    
  def get_logreadings(self):
    """Returns the number of readings per log record"""
    logset = self.visa_query("LOGSET?")
    
    return string.atoi(logset.split(",")[4])
    
    
  def get_logunits(self, reading):
    """Returns the unit string for a reading within each log record"""
    
    retval = self.visa_query("LOGREAD? %d" % reading)
    
    unitnum = retval.split(",")[1]
    
    if unitnum == "1":
        unitstr = "K"
    elif unitnum == "2":
        unitstr = "C"
    elif unitnum == "3":
        unitstr = "S"
    else:
        unitstr = "L"
        
    return unitstr
    
    
  def get_loginput(self, reading):
    """Return the input number for the specified log reading"""
    retval = self.visa_query("LOGREAD? %d" % reading)
    
    inputnum = retval.split(",")[1]
    
    return string.atof(inputnum)
    
    
  def get_temp(self, sensor, unit="K"):
    """Get the current reading from sensor (int), in specified units
    (default is Kelvin).  Returns reading as float.  
    
    Raises exception if sensor is inactive, or if K or C is requested 
    for a sensor with no calibration curve"""
    
    # Check if sensor is active
    if self.sensor_enabled(sensor) != True:
        raise ValueError("LAKESHORE: Sensor %d is not enabled" % sensor)
    
    # If temperature is reqested, check for calibration curve
    if (unit == "K" or unit == "C"):
        if self.sensor_calibrated(sensor) != True:
            raise ValueError("LAKESHORE: Sensor %d has no calibration curve" % sensor)
        
    if unit=="K": # get reading in Kelvin
        reading = self.visa_query("KRDG? %d" % sensor)
        
    elif unit=="C": # get reading in Celsius
        reading = self.visa_query("CRDG? %d" % sensor)
        
    elif unit=="L": # get reading in Linear number
        reading = self.visa_query("LRDG? %d" % sensor)
    else: # get reading in Sensor units
        reading = self.visa_query("SRDG? %d" % sensor)
        
    return string.atof(reading)


  def sensor_enabled(self, sensor):
    """Checks whether sensor (int) is enabled, returns Python Boolean"""
    
    onoff = self.visa_query("INPUT? %d" % sensor)
        
    if onoff == "1":
        return True
    else:
        return False


  def sensor_calibrated(self, sensor):
      """Checks whether sensor (int) has a calibration curve.  Returns
      Python Boolean"""
      
      calibrated = self.visa_query("INCRV? %d" % sensor)
      
      if calibrated == "00":
          return False
      else:
          return True
          
  def get_datetime(self):
      """Gets the data and time from the lakeshore
      - may not be accurate!"""
      datetime = self.visa_query("DATETIME?")
      
      dl = datetime.split(",")
      
      return "%s/%s/%s;%s:%s:%s" % (dl[1], dl[0], dl[2], dl[3], dl[4], dl[5])
      
  def write_log(self, filename, log):
      """Write the contents of the log object returned by get_log() to a
      file
      
      File is tab seperated."""
      
      f = open(filename, "w")
      
      for l in log:
          line = l[0]
          for a in l[1:]:
              line = line + "\t" + str(a)
              
          f.write(line+"\n")

      f.close()
