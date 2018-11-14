# creates a default configuration for a DAQ object

from lib import hjsonConfig
import os

verbose=False

fileName = os.path.join(os.path.dirname(__file__), "config", "IV-default.hjson")
defaultConfig = hjsonConfig.hjsonConfig(fileName=fileName, verbose=verbose)
