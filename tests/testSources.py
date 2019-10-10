'''
Created on May 6, 2017

@author: Guido
'''
import sys
import unittest
from contextlib import closing
import datetime
import xmlrunner
from sqlalchemy.exc import IntegrityError
import sqlalchemy

from utils import dbUtils as db
import movieLogger
import tests.utils

import sources
from movieDbClasses import Locations
from movieDbClasses import SQLite_Master

class testSource(unittest.TestCase):
    """
    Tests for the sources class.
    """

    src = None
    util = None

    _dbName = '/home/guido/work/git/movie-diversity/workingDb.db'

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
                    "title_from_ref integer",
                    "tmdb_id integer"
                   ]
                  }

    @classmethod
    def setUpClass(cls):
        super(testSource, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('DEBUG')

    def setUp(self):
        unittest.TestCase.setUp(self)

        self.src = sources.Sources(dbfile = self._dbName)
        self.util = tests.utils.Utils(dbfile = self._dbName,
                                      logger = self.src.logger)

        self.util.checkDbDataTestNames()

    def tearDown(self):
        # for cleaning, no need to stay at DEBUG level
        movieLogger.MovieLoggger().resetLoggingLevel('INFO')
        self.util.cleanUpTestData()
        movieLogger.MovieLoggger().resetLoggingLevel('DEBUG')
        unittest.TestCase.tearDown(self)

    def testSchema(self):
        """Verifies that the definitions of the db schema conforms to the expectations."""

        self.src.logger.info("Verifying db schema tables...")

        allTables = self.src.getAllTablesDefinitions()

        assert len(allTables) == 6, \
            "%s file should have 6 tables defined (found %d)." % (self._dbName, len(allTables))

        assert isinstance(allTables, type([])), \
            "Expected a list of sqlite3.Row, got instead %s" % (type(allTables))
        assert len(allTables) > 0, \
            "Expected at least one element in the list, got 0"
        assert isinstance(allTables[0], SQLite_Master), \
            "Expected elements of sqlalchemy.SSQLite_Master, got instead %s" % (type(allTables[0]))
        tablesNames = self._schemaData.keys()

        # we look in all the tables defined in the schemaData dictionary
        # to find the expected elements. This guarantees the minimum data
        # needed to work correctly.
        for tName in tablesNames:
            stmt = [x.sql.lower() for x in allTables if "create table " + tName + " (" in x.sql.lower()]

            self.src.logger.debug("\tVerifying definition for table %s", tName)
            assert len(stmt) == 1 and ("create table %s" % tName) in stmt[0], \
                "Table %s not found in schema." % tName

            for c in self._schemaData[tName]:
                self.src.logger.debug("\tVerifying column %s in table %s", c, tName)
                assert c in stmt[0], \
                    "Declaration for '%s' not found in table %s.\n schD = %s\nstmt = %s" % \
                    (c, tName, self._schemaData[tName], stmt[0])
        self.src.logger.info("Schema verification terminated and passed.")

    def testPlacesType(self):
        """Tests the places metadata."""
        self.src.logger.debug("Verifying definition for Locations wrapper class.")

        places = self.src.getAllLocations(refresh = True)

        self.src.logger.debug("\tChecking getAllLocations() returning a list.")
        self.assertTrue(isinstance(places, list) and places != [], \
                        "getAllLocations() should return a list.")

        self.src.logger.debug("\tChecking getAllLocations() returning a list of Locations.")
        self.assertTrue(isinstance(places[0], Locations) and places != [], \
                        "getAllLocations() should return a list of Locations.")

        self.src.logger.debug("\tChecking instances having the right columns.")
        self.assertTrue(sorted(places[0].getColumnNames()) == sorted(['id', 'name', 'language']),
                        "getAllLocations() should return a list of Locations whose keys are 'id', 'language' and 'name'.")

        self.src.logger.debug("Verification for Locations wrapper class passed.")

    def testPlacesNames(self):
        """Tests the places names data."""
        self.src.logger.debug("Verification of Locations seed data.")

        places = [x.name for x in self.src.getAllLocations(refresh = True)]

        self.assertIn("Milano", places, "Milano should be included in the places list.")
        self.assertIn("San Francisco", places, "San Francisco should be included in the places list.")
        self.assertIn("New York", places, "New York should be included in the places list.")
        self.assertIn("Cairo", places, "Cairo should be included in the places list.")
        self.assertIn("München", places, "München should be included in the places list.")

        self.src.logger.debug("Verification for Locations seed data passed.")

    def testLocationsSitesData(self):
        """Tests the locations and sites data."""
        self.src.logger.debug("Verification of Locations and sites data.")

        locationsSites = [x['name'] for x in self.src.getLocationSitesData("Milano", refresh = True)]

        self.assertIn("film.it", locationsSites, "film.it should be included in the places list.")
        self.assertIn("mymovies.it", locationsSites, "mymovies.it should be included in the places list.")

        self.src.logger.debug("Verification for Locations seed data passed.")

    def testTitlesData(self):
        """Tests the getAllTitles."""
        self.src.logger.debug("Verification of getAllTitles.")

        allTitles = [t.title for t in self.src.getAllTitles()]
        self.assertIn("Il diritto di contare", allTitles, "'Il diritto di contare' should be included in the places list.")

        self.src.logger.debug("Verification for getAllTitles passed.")

    def testInsertTitleInLocation(self):
        """Tests inserting a test title in a location."""
        self.src.logger.debug("Verification of inserting a title in a given location.")

        testTitle = self.util.getNewTestName()
        self.src.logger.debug("\tInserting %s in location 1." % (testTitle))
        (tid1, tilid1) = self.src.insertTitleInLocation(aTitle = testTitle,
                                                        locationId = 1)
        self.assertTrue(isinstance(tid1, int), 'Id for titles should be returned as an integer (got: %s).' % tid1)
        self.assertTrue(isinstance(tilid1, int), 'Id for titlesInLocations should be returned as an integer (got: %s).' % tilid1)

        self.src.logger.debug("\tRe-inserting the same %s in location 1." % (testTitle))
        (tid2, tilid2) = self.src.insertTitleInLocation(aTitle = testTitle,
                                                        locationId = 1)
        self.assertTrue(isinstance(tid2, int), 'Id for titles in new location should be returned as an integer (got: %s).' % tid2)
        self.assertTrue(isinstance(tilid2, int), 'Id for titlesInLocation in new location should be returned as an integer (got: %s).' % tilid2)
        self.assertTrue(tid1 == tid2, 'Second insertion should return the original title id (%s, got: %s).' % (tid1, tid2))
        self.assertTrue(tilid1 == tilid2, 'Second insertion should return the original TiL id (%s, got: %s).' % (tid1, tid2))

        self.src.logger.debug("\tInserting %s in location 2." % (testTitle))
        (tid3, tilid3) = self.src.insertTitleInLocation(aTitle = testTitle,
                                                        locationId = 2)
        self.assertTrue(isinstance(tid3, int), 'Id for titles in new location should be returned as an integer (got: %s).' % tid3)
        self.assertTrue(isinstance(tilid3, int), 'Id for titlesInLocation in new location should be returned as an integer (got: %s).' % tilid3)
        self.assertTrue(tid1 == tid3, 'Insertion in new location should return the original title id (%s, got: %s).' % (tid1, tid2))
        self.assertTrue(tilid3 != tilid1, 'Insertion in new location should return a new TiL id (got again: %s).' % (tilid3))

        try:
            self.src.logger.debug("\tNegative case: inserting %s in location 1." % (None))
            (tid1, tilid1) = self.src.insertTitleInLocation(aTitle = None, locationId = 1)
            self.fail('Inserting a null title should throw an exception. Got (tid, tilid) = (%d, %d)' % (tid1, tilid1))

        except AssertionError:
            self.src.logger.info("IntegrityError thrown by the db as expected for NULL title.")
        except AttributeError:
            self.src.logger.info("AttributeError thrown by the util as expected for NULL title.")

        try:
            testTitle = self.util.getNewTestName()
            self.src.logger.debug("\tNegative case: inserting %s in NULL location." % (testTitle))
            (tid1, tilid1) = self.src.insertTitleInLocation(aTitle = testTitle, locationId = None)
            self.fail('Inserting a null location should throw an exception. . Got (tid, tilid) = (%d, %d)' % (tid1, tilid1))

        except AssertionError:
            self.src.logger.info("IntegrityError thrown by the db as expected for NULL location.")

        try:
            testTitle = self.util.getNewTestName()
            self.src.logger.debug("\tNegative case: inserting %s in location -1." % (testTitle))
            (tid1, tilid1) = self.src.insertTitleInLocation(aTitle = testTitle, locationId = -1)
            self.fail('Inserting an invalid location should throw an exception. . Got (tid, tilid) = (%d, %d)' % (tid1, tilid1))

        except IntegrityError:
            self.src.logger.info("IntegrityError thrown by the db as expected for invalid location.")

    def testInsertShow(self):
        """Tests inserting a show with a test title in a location."""
        testTitle = self.util.getNewTestName()
        testTitleId = self.src.insertTitleInLocation(aTitle = testTitle, locationId = 1)[0]

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
                        "Fourth insertion with tomorrow's explicit date should return a new id (%s, %s, got: %s)." \
                        % (id1, id3, id4))

        # happy path today date new location
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
                self.src.logger.info("IntegrityError thrown by the db as expected for NULL title (default date).")
                self.src.rollbackSession()
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = None, locationsRef = 1, date = yesterday)
            self.fail('Inserting a null titlesRef (explicit date) should throw an exception. Got record %d' % id1)

        except AssertionError as ae:
            if str(ae) == "Cannot insert a show with a null titlesRef!":
                self.src.logger.info("IntegrityError thrown by the db as expected for NULL title (yesterday's date).")
                self.src.rollbackSession()
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = -1, locationsRef = 1, date = today)
            self.assertEqual(id1, 65813, 'Inserting an invalid titlesRef (0, with explicit date) should throw an exception. Got record %d' % id1)

        except IntegrityError as ie:
            if str(ie).startswith("(sqlite3.IntegrityError) FOREIGN KEY constraint failed"):
                self.src.logger.info("IntegrityError thrown by the db as expected for invalid title (today's date).")
                self.src.rollbackSession()
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = id5, locationsRef = None, date = yesterday)
            self.fail('Inserting a null locationsRef (explicit date) should throw an exception. Got record %d' % id1)

        except AssertionError as ae:
            if str(ae) == "Cannot insert a show with a null locationsRef!":
                self.src.logger.info("AssertionError thrown by the db as expected for NULL location (yesterday's date).")
            else:
                self.src.logger.error("Got the following error message: '%s'", ae)
                raise

        try:
            id1 = self.src.insertShow(titlesRef = id5, locationsRef = 0, date = yesterday)
            self.fail('Inserting an invalid locationsRef (0, explicit date) should throw an exception. Got record %d' % id1)

        except IntegrityError as ie:
            if str(ie).startswith("(sqlite3.IntegrityError) FOREIGN KEY constraint failed"):
                self.src.logger.info("IntegrityError thrown by the db as expected for NULL location (yesterday's date).")
                self.src.rollbackSession()
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

