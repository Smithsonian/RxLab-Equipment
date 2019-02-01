# creates a default configuration for a DAQ object

from LabEquipment.lib import hjsonConfig

from pkg_resources import resource_filename

verbose=False

filename = resource_filename("LabEquipment", "config/IVP_timestream-default.hjson")
if verbose:
    print("_default_IVP_timestream_config: Reading Default configFile: ", filename)
defaultConfig = hjsonConfig.hjsonConfig(filename=filename, verbose=verbose)
