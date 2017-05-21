'''
Created on May 6, 2017

@author: Guido
'''
import sys
import unittest
import scraper

class testScraper(unittest.TestCase):

    src = None
    scaper = None
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.scaper = scraper.Scraper()
        
    def testGetMovieTitles(self):
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        import xmlrunner
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))

