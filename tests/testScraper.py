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
    scraper = None

    _dbName = '/home/guido/work/git/movie-diversity/wirkingDb.db'

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.scraper = scraper.Scraper(dbfile = self._dbName)

    def testGetMovieTitles(self):
        """
        Missing implementation.
        """
        pass
        # self.fail("testGetMovieTitles has not been implemented yet!")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports'))

