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
import sourcesAlchemy
import movieLogger
import tests.utils

import sources
from movieDbClasses import Locations

class testSourceAlchemy(unittest.TestCase):
    """
    Tests for the sources class.
    """

    src = None
    oldSrc = None
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
        super(testSourceAlchemy, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('DEBUG')

    def setUp(self):
        unittest.TestCase.setUp(self)

        self.src = sourcesAlchemy.SourcesAlchemy(dbfile = self._dbName)
        self.oldSrc = sources.Sources(dbfile = self._dbName)

        self.util = tests.utils.Utils(dbfile = self._dbName,
                                      logger = self.src.logger)

        self.util.checkDbDataTestNames()

    def tearDown(self):
        self.util.cleanUpTestData()
        unittest.TestCase.tearDown(self)

    def testSchema(self):
        """Verifies that the definitions of the db schema conforms to the expectations.
        """

        self.oldSrc.logger.info("Verifying db schema tables...")

        with (closing(db.cursor(self.oldSrc._conn))) as cur:
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
        """
        Tests the places metadata.
        """
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
        """
        Tests the places names data.
        """
        self.src.logger.debug("Verification of Locations seed data.")

        places = [x.name for x in self.src.getAllLocations(refresh = True)]

        self.assertIn("Milano", places, "Milano should be included in the places list.")
        self.assertIn("San Francisco", places, "San Francisco should be included in the places list.")
        self.assertIn("New York", places, "New York should be included in the places list.")
        self.assertIn("Cairo", places, "Cairo should be included in the places list.")
        self.assertIn("München", places, "München should be included in the places list.")

        self.src.logger.debug("Verification for Locations seed data passed.")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports'))

