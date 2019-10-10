'''
Created on October 9, 2019

@author: Guido
'''
from utils.propertiesFileReader import PropertiesFileReader
import sys
import xmlrunner
import movieLogger
import logging
import unittest
import tempfile

class testPropertiesReader(unittest.TestCase):
    """
    Tests for the properties file reader.
    """
    _PROP_FILE = """# sample one
 # sample two
Login=yes
URL = https://example.com
 number= 1

passphrase= Once upon a time in America
b = False
 = pippo
"""

    logger = None
    reader = None
    tempPropFile = None

    @classmethod
    def setUpClass(cls):
        super(testPropertiesReader, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('INFO')

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)
        self.reader = PropertiesFileReader()

        self.tempPropFile = tempfile.NamedTemporaryFile(mode = 'w+t')
        self.logger.info("Creating new temp file %s" % (self.tempPropFile.name))
        self.tempPropFile.write(self._PROP_FILE)
        self.tempPropFile.flush()
        self.logger.info("Created temp file %s" % (self.tempPropFile.name))

    def tearDown(self):
        # for cleaning, no need to stay at DEBUG level
        self.tempPropFile.close()
        self.logger.info("Deleted temp file %s" % (self.tempPropFile.name))

        unittest.TestCase.tearDown(self)

    def testReadAFile(self):
        nvp = self.reader.readPropertiesFile(self.tempPropFile.name)
        self.assertEqual(len(nvp), 5, "Expected 5 pairs, got %d" % (len(nvp)))
        self.assertEqual(nvp['Login'], "yes", "Login should be = yes")
        self.assertEqual(nvp['passphrase'], "Once upon a time in America", "passphrase should be = \"Once upon a time in America\"")
        self.assertEqual(nvp['URL'], "https://example.com", "URL should be = \"https://example.com\"")
        self.assertEqual(nvp['b'], "False", "b should be = \"False\"")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports'))

