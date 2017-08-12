'''
Created on May 6, 2017

@author: Guido
'''
import sys
import unittest
import xmlrunner
import scraper

class testScraper(unittest.TestCase):
    """
    Test for the scraper class.

    Currently does nothing.
    """

    src = None
    scaper = None

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.scaper = scraper.Scraper()

    def testGetMovieTitles(self):
        """
        Missing implementation.
        """
        self.fail("testGetMovieTitles has not been implemented yet!")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))

