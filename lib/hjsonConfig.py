# H

import os
import jsonmerge
import hjson

class hjsonConfig:
    """A class to handle reading configurations in hjson files, which
    may include references to other hjson files via "config-file" entries.

    Entries duplicated in the top level file override the entries in an included file."""
    def __init__(self, fileName=None, verbose=False, dir=None):
        """Very basic set up"""
        self.verbose = verbose
        self.dir = dir
        if fileName != None:
            self.config = self.importConfigFiles(self.readFile(fileName))

    def readFile(self, fileName):
        """Read the .hjson configuration file"""
        # Opens use file and assigns corresponding parameters
        if self.verbose:
            print("Reading config file: ", fileName)
        try:
            if dir != None:
                fileName = os.path.join(dir, fileName)
            f = open(fileName, 'r')
            newConfig = hjson.load(f)
            f.close()
            return newConfig
        except FileError:
            if self.verbose:
                print("Config file {:s} not found.".format(fileName))
            return None


    def importConfigFiles(self, config):
        """Merge passed config into referenced config files if present.

        Entries in  the passed config overwrite any entries read from the file.
        This allows this function to be called recursively to build up a complete config."""
        # If a config json OrderedDict is passed, merge it with the existing configuration
        # Try and parse a config-file if it is passed to us
        if config = None:
            return None

        try:
            if config["config-file"] != None:
                configFile = config["config-file"]
                config["config-file"] = None
        except KeyError:
            configFile = None

        if configFile != None:
            fileConfig = self.readFile(configFile)

        if config != None:
            config = mergejson.merge(fileConfig, config)
        else:
            config = fileConfig

        return importConfigFiles(config)
