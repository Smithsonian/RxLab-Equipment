# creates a default configuration for a DAQ object

from lib import hjsonConfig

from pkg_resources import resource_filename

verbose=False

filename = resource_filename("LabEquipment", "config/IV-default.hjson")

if verbose:
    print("_default_IV_config: Reading Default configFile: ", filename)
defaultConfig = hjsonConfig.hjsonConfig(filename=filename, verbose=verbose)
