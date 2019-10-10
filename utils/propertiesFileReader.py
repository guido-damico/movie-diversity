'''
Created on Oct 9, 2019

Simple reader for java-style properties files.
It expects name-value paris, one per line, separated by "=".
It ignore all the comment line which begins with "#".

@author: Guido
'''
import logging
import movieLogger

class PropertiesFileReader(object):
    logger = None

    def __init__(self, params = None):
        """
        Constructor. Inits the logger.
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

    def readPropertiesFile(self, fileName = None):
        """
        Reads a .properties file in and returns a dictionary with all the name/value pairs.
        Comments (lines which begins with "#") are ignored.
        """
        output = {}

        if fileName == None:
            return None

        with open(fileName, "rt") as fp:
            lineNo = 0;

            for aLine in fp.readlines():
                lineNo += 1
                aLine = aLine.strip()

                # skip comments
                if len(aLine) == 0 or aLine[0] == "#":
                    continue

                nvp = aLine.split("=")
                if len(nvp) != 2:
                    self.logger.error("Cannot parse line %d from %s: \"%s\"" % (lineNo, fileName, aLine))

                else:
                    if nvp[0] == '':
                        self.logger.error("Cannot parse line %d from %s: \"%s\"" % (lineNo, fileName, aLine))
                        continue
                    output[nvp[0].strip()] = nvp[1].strip()

        return output
