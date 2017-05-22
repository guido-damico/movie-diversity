'''
Created on May 6, 2017

@author: Guido
'''
import sys
import sqlite3
import unittest
import datetime
import sources
import movieLogger
import tests.utils as utils

class testSource(unittest.TestCase):

    src = None
    util = None

    _dbName = '/home/guido/work/git/movie-diversity/movieDiversity.db'

    @classmethod
    def setUpClass(cls):
        super(testSource, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('INFO')

    def setUp(self):
        unittest.TestCase.setUp(self)

        self.src = sources.Sources(dbfile = self._dbName)

        self.util = utils.Utils(dbfile = self._dbName,
                                logger = self.src.logger)
        self.util.checkDbDataTestNames()

    def tearDown(self):
        self.util.cleanUpTestData()
        unittest.TestCase.tearDown(self)

    def testPlacesType(self):
        places = self.src.getAllLocations(refresh = True)

        self.assertTrue(isinstance(places, type([])) and
                        places != [],
                        "getAllPlaces() should return a list of strings.")

    def testPlacesNames(self):
        places = self.src.getAllLocations(refresh = True)

        self.assertIn("Milano", places, "Milano should be included in the places list.")
        self.assertIn("San Francisco", places, "San Francisco should be included in the places list.")

    def testSeedData(self):
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
                self.assertEqual(frozenset(data.keys()),\
                                 frozenset(['id', 'name', 'url', 'title_xpath', 'active', 'locations_ref', 'location_name']),
                                 "keys for first element of %s are not correct (found: %s)" % (town, data.keys()))

                self.assertTrue(isinstance(data['name'], type("")),
                                "site value for %s should be a string (was %s)" % (town, type(data['name'])))
                self.assertTrue(len(data['name']) > 0,
                                "site value for %s should not be a an empty string" % (town))

                self.assertTrue(isinstance(data['title_xpath'], type("")),
                                "title_xpath value for %s should be a string (was %s)" % (town, type(data['title_xpath'])))
                self.assertTrue(len(data['title_xpath']) > 0,
                                "title_xpath value for %s should not be a an empty string" % (town))

    def testInsertTitle(self):
        testTitle = self.util.getNewTestName()
        id1 = self.src.insertTitle(title = testTitle,
                                   locationId=1)
        self.assertTrue(isinstance(id1, type(1)), 'Id for titles should be returned as an integer (got: %s).' % id1)
       
        id2 = self.src.insertTitle(title = testTitle,
                                   locationId=1)
        self.assertTrue(id1 == id2, 'Second insertion should return the original id (%s, got: %s).' %(id1, id2))

        try:
            id1 = self.src.insertTitle(title = None, locationId = 1)
            self.fail('Inserting a null title should throw an exception. Got record %d' % id1)

        except sqlite3.IntegrityError:
            pass

        try:
            id1 = self.src.insertTitle(title = testTitle, locationId = None)
            self.fail('Inserting a null location should throw an exception. Got record %d' % id1)

        except sqlite3.IntegrityError:
            pass

        try:
            id1 = self.src.insertTitle(title = testTitle, locationId = -1)
            self.fail('Inserting an invalid location should throw an exception. Got record %d' % id1)

        except sqlite3.IntegrityError:
            pass

    def testInsertShow(self):
        testTitle = self.util.getNewTestName()
        testTitleId = self.src.insertTitle(title = testTitle, locationId = 1)

        today = datetime.date.today().strftime('%Y-%m-%d')
        yesterday = (datetime.date.today() - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.date.today() + datetime.timedelta(days = 1)).strftime('%Y-%m-%d')

        id1 = self.src.insertShow(titlesRef = testTitleId, date = None)
        self.assertTrue(isinstance(id1, type(1)), 'Id for shows should be returned as an integer (got: %s).' % id1)

        id2 = self.src.insertShow(titlesRef = testTitleId, date = None)
        self.assertTrue(id1 == id2, 'Second insertion with None date should return the original id (%s, got: %s).' %(id1, id2))

        id2 = self.src.insertShow(titlesRef = testTitleId, date = today)
        self.assertTrue(id1 == id2, "Second insertion with today's explicit date should return the original id (%s, got: %s)." %(id1, id2))

        id3 = self.src.insertShow(titlesRef = testTitleId, date = yesterday)
        self.assertTrue(id1 != id3, "Third insertion with yesteday's explicit date should return a new id (%s, got: %s)." %(id1, id2))

        id4 = self.src.insertShow(titlesRef = testTitleId, date = tomorrow)
        self.assertTrue(id1 != id4 and id3 != id4, "Fourth insertion with today's explicit date should return a new id (%s, got: %s)." %(id1, id2))

        try:
            id1 = self.src.insertShow(titlesRef = None, date = None)
            self.fail('Inserting a null titles_ref (Null date) should throw an exception. Got record %d.' % id1)

        except sqlite3.IntegrityError:
            pass

        try:
            id1 = self.src.insertShow(titlesRef = None, date = today)
            self.fail('Inserting a null titles_ref (explicit date) should throw an exception. Got record %d' % id1)

        except sqlite3.IntegrityError:
            pass        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        import xmlrunner
        del sys.argv[1] # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))

