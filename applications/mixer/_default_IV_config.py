# creates a default configuration for a DAQ object

from lib import hjsonConfig
import os
from pathlib import Path

verbose=False

fileName = os.path.join(Path(__file__).resolve().parents[0], "config", "IV-default.hjson")
if verbose:
    print("_default_IV_config: Reading Default configFile: ", fileName)
defaultConfig = hjsonConfig.hjsonConfig(fileName=fileName, verbose=verbose)
