'''
Created on May 6, 2017

@author: Guido
'''
import sys
import sqlite3
import unittest
import datetime
from contextlib import closing
import xmlrunner
from utils import dbUtils as db
import sources
import movieLogger
import tests.utils

class testSource(unittest.TestCase):
    """
    Tests for the sources class.
    """

    src = None
    util = None

    _dbName = '/home/guido/work/git/movie-diversity/movieDiversity.db'

    # schema verification info: will be used at the beginning
    # to ensure the db is seeded correctly
    _schemaData = {'locations':
                   ["id integer primary key",
                    "name text",
                    "language text"],
                   'sites':
                   ["id integer primary key",
                    "name text",
                    "url text",
                    "title_xpath text",
                    "active integer",
                    "locations_ref integer"],
                   'titles':
                   ["id integer primary key",
                    "title text",
                   ],
                   'titles_in_locations':
                   ["id integer primary key",
                    "titles_ref integer",
                    "locations_ref integer",
                   ],
                   'shows':
                   ["id integer primary key",
                    "date text",
                    "titles_in_locations_ref integer"
                   ],
                   'translations':
                   ["id integer primary key",
                    "lang_from text",
                    "lang_to text",
                    "title_from_ref integer",
                    "title_to_ref integer"
                   ]
                  }

    @classmethod
    def setUpClass(cls):
        super(testSource, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('INFO')

    def setUp(self):
        unittest.TestCase.setUp(self)

        self.src = sources.Sources(dbfile = self._dbName)

        self.util = tests.utils.Utils(dbfile = self._dbName,
                                      logger = self.src.logger)

        self.util.checkDbDataTestNames()

    def tearDown(self):
        self.util.cleanUpTestData()
        unittest.TestCase.tearDown(self)

    def testSchema(self):
        """
        Verifies that the definitions of the db schema conforms to the expectations.
        """

        self.src.logger.info("Verifying db schema tables...")

        with (closing(db.cursor(self.src._conn))) as cur:
            cur.execute("SELECT lower(sql) sql FROM sqlite_master;")
            allTables = cur.fetchall()

            assert len(allTables) == 6, \
                "%s file should have 5 tables defined (found %d)." % (self._dbName, len(allTables))

            assert isinstance(allTables, type([])), \
                "Expected a list of sqlite3.Row, got instead %s" % (type(allTables))
            assert len(allTables) > 0, \
                "Expected at least one element in the list, got 0"
            assert isinstance(allTables[0], sqlite3.Row), \
                "Expected elements of sqlite3.Row, got instead %s" % (type(allTables[0]))
            tablesNames = self._schemaData.keys()

            # we look in all the tables defined in the schemaData dictionary
            # to find the expected elements. This guarantees the minimum data
            # needed to work correctly.
            for tName in tablesNames:
                stmt = [x[0] for x in allTables if "create table " + tName + " (" in x[0]]

                self.src.logger.debug("Verifying definition for table %s", tName)
                assert len(stmt) == 1 and ("create table %s" % tName) in stmt[0], \
                    "Table %s not found in schema." % tName

                for c in self._schemaData[tName]:
                    self.src.logger.debug("Verifying column %s in table %s", c, tName)
                    assert c in stmt[0], \
                        "Declaration for '%s' not found in table %s.\n schD = %s\nstmt = %s" % \
                        (c, tName, self._schemaData[tName], stmt[0])
            self.src.logger.info("Verification terminated and passed.")

    def testPlacesType(self):
        """
        Tests the places metadata.
        """
        places = self.src.getAllLocations(refresh = True)

        self.assertTrue(isinstance(places, list) and places != [], \
                        "getAllLocations() should return a list.")

        self.assertTrue(isinstance(places[0], dict) and places != [], \
                        "getAllLocations() should return a list of dictionaries.")

        self.assertTrue(sorted(list(places[0].keys())) == sorted(['id', 'name']),
                        "getAllLocations() should return a list of dictionaries whose keys are 'id' and 'name'.")

    def testPlacesNames(self):
        """
        Tests the places names data.
        """
        places = [x['name'] for x in self.src.getAllLocations(refresh = True)]

        self.assertIn("Milano", places, "Milano should be included in the places list.")
        self.assertIn("San Francisco", places, "San Francisco should be included in the places list.")
        self.assertIn("New York", places, "New York should be included in the places list.")
        self.assertIn("Cairo", places, "Cairo should be included in the places list.")
        self.assertIn("München", places, "München should be included in the places list.")

    def testSeedData(self):
        """
        Tests the seed data for all places.
        """
        places = self.src.getAllLocations(refresh = True)

        for town in places:
            placeData = self.src.getLocationData(town['name'], refresh = True)

            self.assertTrue(isinstance(placeData, type([])),
                            "data for %s should be a list (was %s)" % (town, type(placeData)))
            self.assertTrue(len(placeData) > 0,
                            "data for %s should have at least one element" % (town))

            for data in placeData:
                self.assertTrue(isinstance(data, type({})),
                                "data for first element of %s should be a dictionary (was %s)" % (town, type(data)))
                self.assertEqual(frozenset(data.keys()), \
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

    def testInsertTitleInLocation(self):
        """
        Tests inserting a test title in a location.
        """
        testTitle = self.util.getNewTestName()
        (tid1, tilid1) = self.src.insertTitleInLocation(title = testTitle,
                                                        locationId = 1)
        self.assertTrue(isinstance(tid1, int), 'Id for titles should be returned as an integer (got: %s).' % tid1)

        (tid2, tilid2) = self.src.insertTitleInLocation(title = testTitle,
                                                        locationId = 1)
        self.assertTrue(tid1 == tid2, 'Second insertion should return the original id (%s, got: %s).' % (tid1, tid2))

        try:
            (tid1, tilid1) = self.src.insertTitleInLocation(title = None, locationId = 1)
            self.fail('Inserting a null title should throw an exception. Got (tid, tilid) = (%d, %d)' % (tid1, tilid1))

        except AssertionError:
            self.src.logger.info("IntegrityError thrown by the db as expected for NULL title.")
        except AttributeError:
            self.src.logger.info("AttributeError thrown by the util as expected for NULL title.")

        try:
            testTitle = self.util.getNewTestName()
            (tid1, tilid1) = self.src.insertTitleInLocation(title = testTitle, locationId = None)
            self.fail('Inserting a null location should throw an exception. . Got (tid, tilid) = (%d, %d)' % (tid1, tilid1))

        except AssertionError:
            pass

        try:
            testTitle = self.util.getNewTestName()
            (tid1, tilid1) = self.src.insertTitleInLocation(title = testTitle, locationId = -1)
            self.fail('Inserting an invalid location should throw an exception. . Got (tid, tilid) = (%d, %d)' % (tid1, tilid1))

        except sqlite3.IntegrityError:
            pass

    def testInsertShow(self):
        """
        Tests inserting a show with a test title in a location.
        """
        testTitle = self.util.getNewTestName()
        testTitleId = self.src.insertTitleInLocation(title = testTitle, locationId = 1)[0]

        today = datetime.date.today().strftime('%Y-%m-%d')
        yesterday = (datetime.date.today() - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.date.today() + datetime.timedelta(days = 1)).strftime('%Y-%m-%d')

        # happy paths default date
        id1 = self.src.insertShow(titlesRef = testTitleId, locationsRef = 1, date = None)
        self.assertTrue(isinstance(id1, int), \
                        'Id for shows should be returned as an integer (got: %s).' % id1)

        id2 = self.src.insertShow(titlesRef = testTitleId, locationsRef = 1, date = None)
        self.assertTrue(id1 == id2, \
                        'Second insertion with None date should return the original id (%s, got: %s).' % (id1, id2))

        # happy paths explicit date
        id2 = self.src.insertShow(titlesRef = testTitleId, locationsRef = 1, date = today)
        self.assertTrue(id1 == id2, \
                        "Second insertion with today's explicit date should return the original id (%s, got: %s)." % (id1, id2))

        id3 = self.src.insertShow(titlesRef = testTitleId, locationsRef = 1, date = yesterday)
        self.assertTrue(id1 != id3, \
                        "Third insertion with yesteday's explicit date should return a new id (%s, got: %s)." % (id1, id3))

        id4 = self.src.insertShow(titlesRef = testTitleId, locationsRef = 1, date = tomorrow)
        self.assertTrue(id1 != id4 and id3 != id4, \
                        "Fourth insertion with today's explicit date should return a new id (%s, %s, got: %s)." \
                        % (id1, id3, id4))

        # happy path default date new location
        id5 = self.src.insertShow(titlesRef = testTitleId, locationsRef = 2, date = today)
        self.assertTrue(id1 != id5 and id3 != id5 and id4 != id5, \
                        "Fifth insertion with today's explicit date but a new location should return a new id (%s, %s, %s, got: %s)." \
                        % (id1, id3, id4, id5))

        # sad paths
        try:
            id1 = self.src.insertShow(titlesRef = None, locationsRef = 1, date = None)
            self.fail('Inserting a null titlesRef (Null date) should throw an exception. Got record %d.' % id1)

        except AssertionError as ae:
            if str(ae) == "Cannot insert a show with a null titlesRef!":
                pass
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = None, locationsRef = 1, date = today)
            self.fail('Inserting a null titlesRef (explicit date) should throw an exception. Got record %d' % id1)

        except AssertionError as ae:
            if str(ae) == "Cannot insert a show with a null titlesRef!":
                pass
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = -1, locationsRef = 1, date = today)
            self.assertEqual(id1, 65813, 'Inserting an invalid titlesRef (0, with explicit date) should throw an exception. Got record %d' % id1)

        except sqlite3.IntegrityError as ie:
            if str(ie) == "FOREIGN KEY constraint failed":
                pass
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = id5, locationsRef = None, date = today)
            self.fail('Inserting a null locationsRef (explicit date) should throw an exception. Got record %d' % id1)

        except AssertionError as ae:
            if str(ae) == "Cannot insert a show with a null locationsRef!":
                pass
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = id5, locationsRef = 0, date = today)
            self.fail('Inserting an invalid locationsRef (0, explicit date) should throw an exception. Got record %d' % id1)

        except sqlite3.IntegrityError as ie:
            if str(ie) == "FOREIGN KEY constraint failed":
                pass
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports'))

