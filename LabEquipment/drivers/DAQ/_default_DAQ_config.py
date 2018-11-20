# creates a default configuration for a DAQ object

from lib import hjsonConfig
from pkg_resources import resource_filename

verbose=False

fileName = resource_filename(__name__, "config/DAQ-default.hjson")
defaultConfig = hjsonConfig.hjsonConfig(fileName=fileName, verbose=verbose)
