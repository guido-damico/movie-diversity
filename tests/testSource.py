'''
Created on May 6, 2017

@author: guido
'''
import sys
import unittest
import scraper

class testSource(unittest.TestCase):

    src = None
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.src = scraper.Sources()

    def testPlacesType(self):
        places = self.src.getAllLocations(refresh = True)

        self.assertTrue(isinstance(places, type([])) and
                        places != [],
                        "getAllPlaces() should return a list of strings.")

    def testPlacesNames(self):
        places = self.src.getAllLocations(refresh = True)

        self.assertIn("Milano", places, "Milano should be included in the places list.")
        self.assertIn("San Francisco", places, "San Francisco should be included in the places list.")
        
    def testData(self):
        places = self.src.getAllLocations(refresh = True)
        
        for town in places:
            placeData = self.src.getLocationData(town, refresh = True)

            self.assertTrue(isinstance(placeData, type([])),
                            "data for %s should be a list (was %s)" % (town, type(placeData)))
            self.assertTrue(len(placeData) > 0,
                            "data for %s should have at least one element" % (town))
            
            for data in placeData:
                self.assertTrue(isinstance(data, type({})),
                                "data for first element of %s should be a dictionary (was %s)" % (town, type(data)))
                self.assertEqual(frozenset(data.keys()), frozenset(['id', 'name', 'url', 'title_xpath', 'active', 'location_name']),
                                "keys for first element of %s are not correct (found: %s)" % (town, data.keys()))
    
                self.assertTrue(isinstance(data['name'], type("")),
                                "site value for %s should be a string (was %s)" % (town, type(data['name'])))
                self.assertTrue(len(data['name']) >0 ,
                                "site value for %s should not be a an empty string" % (town))
    
                self.assertTrue(isinstance(data['title_xpath'], type("")),
                                "title_xpath value for %s should be a string (was %s)" % (town, type(data['title_xpath'])))
                self.assertTrue(len(data['title_xpath']) >0 ,
                                "title_xpath value for %s should not be a an empty string" % (town))

class testScraper(unittest.TestCase):

    src = None
    scaper = None
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.src = scraper.Sources()
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

