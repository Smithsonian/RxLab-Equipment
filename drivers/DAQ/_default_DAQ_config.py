# creates a default configuration for a DAQ object

from lib import hjsonConfig
import os

fileName = os.path.join(os.path.dirname(__file__), "config/DAQ_default.hjson")
defaultConfig = hjsonConfig.hjsonConfig(fileName=fileName)
