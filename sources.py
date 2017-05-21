'''
Created on May 5, 2017

@author: Guido

Source module for the MovieDiversity app.
'''
import sqlite3
import logging
import datetime
import movieLogger
from contextlib import closing

class Sources(object):
    """
        Implementation of the sources to be used with Scraper.
        All db-level actions (towards sqlite) are defined here.

        It depends on movieLogger.MovieLogger.
    """

    logger = None
    _conn = None
    _locations = []
    _data = []

    # sqlite db location
    _sqliteFileName = './movieDiversity.db'
    
    # auto-commit?
    _isolationLevel = None

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
                    "locations_ref integer"
                   ],
                   'shows':
                   ["id integer primary key",
                    "date text",
                    "titles_ref integer"
                   ],
                   'translations':
                   ["id integer primary key",
                    "lang_from text",
                    "lang_to text",
                    "title_from_ref integer",
                    "title_to_ref integer"
                   ]
                  }

    def __init__(self, dbfile = _sqliteFileName):
        """
            Gets a local copy of the logger.
            Connects to the sqlite data db specified by "dbfile" and
            verifies that the schema has been defined correctly.

            The MovieDiversity.sql file contains a valid seeding of the db.
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        self._conn = sqlite3.connect(dbfile, isolation_level = self._isolationLevel)

        self.logger.info("Source connected to db in '%s'", dbfile)

        # in order to get the records and the column names every time, we use
        # the standard Row factory
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.cursor()
        
        # need to enforce the foreign key constraints
        cur.execute("PRAGMA foreign_keys = ON;")

        self.logger.info("Verifying db schema tables...")
        cur.execute("SELECT lower(sql) FROM sqlite_master;")
        allTables = cur.fetchall()
        try:
            assert len(allTables) == 5, \
                "%s file should have 5 tables defined (found %d)." % (dbfile, len(allTables))

            self._verifyFormat(allTables)

        except AssertionError as ae:
            raise AssertionError("Failed db schema validation: execution will stop.\n" + ae.__str__())

    def _verifyFormat(self, allTables = None):
        """Verifies that the definitions of the db schema conforms to the
        expectations of this class.
        """
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
            stmt = [x[0] for x in allTables if "create table " + tName in x[0]]

            self.logger.debug("Verifying definition for table %s", tName)
            assert len(stmt) == 1 and ("create table %s" % tName) in stmt[0], \
                "Table %s not found in schema." % tName

            for c in self._schemaData[tName]:
                self.logger.debug("Verifying column %s in table %s", c, tName)
                assert c in stmt[0], \
                    "Declaration for '%s' not found in table %s.\n schD = %s\nstmt = %s" %\
                    (c, tName, self._schemaData[tName], stmt[0])
        self.logger.info("Verification terminated and passed.")

    def getAllLocations(self,
                        refresh = False):
        """Returns all the locations known to the class up to this point.
        If "Refresh" is set to True, or if there are not locations in the cache,
        performs a new query to the db to get fresh data.
        """
        if refresh or len(self._locations) == 0:
            cur = self._conn.cursor()
            cur.execute('SELECT name FROM locations;')
            self._locations = cur.fetchall()
            self._locations = [x[0] for x in self._locations]

        return self._locations

    def getLocationData(self,
                        location = "",
                        refresh = False):
        """Given a location, it returns all the currently known data for that
        location.
        If "Refresh" is set to True, or if there is no data in the cache,
        performs a new query to the db to get fresh data.

        The data returns is in the form of a list of dictionaries with the
        information about the URL, title_xpath, and Active status of the sites
        connected to the given location.
        """
        if refresh or len(self._data) == 0:
            self.logger.debug("Refreshing data for %s.", location)

            cur = self._conn.cursor()
            cur.execute('SELECT s.id, s.name, url, title_xpath, active, l.name location_name ' + \
                        'FROM locations l, sites s ' + \
                        'WHERE  s.locations_ref = l.id;')
            allData = cur.fetchall()

            for r in allData:
                self._data.append({k: r[k] for k in r.keys()})

        return [x for x in self._data if x['location_name'] == location]

    def insertTitle(self, title = None, locationId = None):
        """Inserts a new title in the db.
        If the same (title , location) tuple is already there, this is a no-op.

        Returns the title primary key.
        """
        with (closing(self._conn.cursor())) as cur:
            cur.execute("SELECT id FROM titles WHERE title = ? AND locations_ref = ?;", (title, locationId))

            titleId = cur.fetchone()
            if titleId != None:
                newId = titleId['id']
            else:
                cur.execute("INSERT INTO titles(title, locations_ref) VALUES (?, ?);", (title, locationId))
                newId = cur.lastrowid

            return newId
                
    def insertShow(self, titlesRef = None, date = None):
        """Inserts a new show for the given titles(id) on the specified date.
        If the same (titles_ref , date) tuple is already there, this is a no-op.
        
        If date is None, then today's date is used.
        The format for the date string should be '%Y-%m-%d'.

        Returns the show primary key.
        """
        currDate = datetime.date.today().strftime('%Y-%m-%d')
        
        if date == None:
            date = currDate

        with (closing(self._conn.cursor())) as cur:
            cur.execute("SELECT id FROM shows WHERE date = ? AND titles_ref = ?;", (date, titlesRef))
            showId = cur.fetchone()

            if showId != None:
                newId = showId['id']
            else:
                cur.execute("INSERT INTO shows(date, titles_ref) VALUES (?, ?);", (date, titlesRef))
                newId = cur.lastrowid

            return newId
    