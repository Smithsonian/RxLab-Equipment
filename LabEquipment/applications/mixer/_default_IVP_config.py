# creates a default configuration for a DAQ object

from lib import hjsonConfig

from pkg_resources import resource_filename

verbose=False

fileName = resource_filename(__name__, "config/IVP-default.hjson")
if verbose:
    print("_default_IVP_config: Reading Default configFile: ", fileName)
defaultConfig = hjsonConfig.hjsonConfig(fileName=fileName, verbose=verbose)
