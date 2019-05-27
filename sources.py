'''
Created on May 5, 2017

@author: Guido

Source module for the MovieDiversity app.
'''
from pprint import pformat
from contextlib import closing
import logging
import datetime
import movieLogger
from utils import stringUtils

from utils import dbUtils as db

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

    def __init__(self, dbfile = _sqliteFileName):
        """
            Gets a local copy of the logger.
            Connects to the sqlite data db specified by "dbfile" and
            verifies that the schema has been defined correctly.

            The MovieDiversity.sql file contains a valid seeding of the db.
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        self._conn = db.connect(dbfile = dbfile)

        self.logger.info("Source connected to db in '%s'", dbfile)

    def getAllLocations(self,
                        refresh = False):
        """Returns all the locations known to the class up to this point.
        If "Refresh" is set to True, or if there are not locations in the cache,
        performs a new query to the db to get fresh data.
        """
        if refresh or len(self._locations) == 0:
            with (closing(db.cursor(self._conn))) as cur:
                cur.execute('SELECT id, name FROM locations;')
                self._locations = cur.fetchall()
                self._locations = [{'id': x['id'], 'name': x['name']} for x in self._locations]

        return self._locations

    def getLocationData(self,
                        locationName = "",
                        refresh = False):
        """Given a location name, it returns all the currently known data for that
        location, in the form of a list of dictionaries.

        If "Refresh" is set to True, or if there is no data in the cache,
        performs a new query to the db to get fresh data.

        The data returned is in the form of a list of dictionaries with the
        information about the URL, title_xpath, and Active status of the sites
        connected to the given location.
        """
        if refresh or len(self._data) == 0:
            self.logger.debug("Refreshing data for %s.", locationName)

            with (closing(db.cursor(self._conn))) as cur:
                cur.execute('SELECT s.id, s.name, url, title_xpath, active, locations_ref, l.name location_name ' + \
                            'FROM locations l, sites s ' + \
                            'WHERE  s.locations_ref = l.id;')
                allData = cur.fetchall()

                for r in allData:
                    self._data.append({k: r[k] for k in r.keys()})

        return [x for x in self._data if x['location_name'] == locationName]

    def getAllDbTitles(self):
        """Returns a list of dictionaries for all titles in the db.

        Valid keys:
            tid : titles(id)
            tilid : titles_in_locations(id)
            title : titles(title)
            locations_ref : locations(id)
        """
        with (closing(db.cursor(self._conn))) as cur:
            cur.execute("""SELECT t.id tid,
                                  t.title title,
                                  l.id locations_ref,
                                  til.id tilid
                           FROM titles t, locations l, titles_in_locations til
                           WHERE t.id = til.titles_ref
                           AND l.id = til.locations_ref;
                        """)

            rows = cur.fetchall()
            output = [{'tid': r['tid'], 'tilid': r['tilid'], 'title': r['title'], 'locations_ref': r['locations_ref']} \
                      for r in rows]

            return output

    def insertTitleInLocation(self, title = None, locationId = None):
        """Inserts a new title for the given location in the db.
        If the same title exists, but in a different location, a new
        record is created in titles_in_locations linking the existing title
        with the new location.

        If the same title exists in the given location, this is a no-op.

        Returns the titles_in_locations record primary key (id).
        """
        newTitleId = None
        newTitleInLocationId = None

        assert title != None and title != "", \
            "Attempted to insert a NULL title!"
        assert locationId != None and isinstance(locationId, int), \
            "Attempted to insert a title with an invalid location (%s)!" % locationId

        with (closing(db.cursor(self._conn))) as cur:
            dbTitles = self.getAllDbTitles()

            # check whether the title is similar to one already in for this location
            similar = [x for x in dbTitles if x['locations_ref'] == locationId \
                                           and (stringUtils.isSimilar(title, x['title']))
                      ]

            if len(similar) == 1:
                # found a similar title already in
                self.logger.debug("Found title '%s', similar to '%s' already in the db: using db version.", \
                                  title, similar[0]['title'])
                newTitleId = similar[0]['tid']
                newTitleInLocationId = similar[0]['tilid']

            elif len(similar) > 1:
                # data inconsistency! Found many similar titles, can't proceed: log an error and discard this record
                self.logger.error("Cannot insert title '%s', found too many similar ones already in the db:\n%s", title, pformat(similar))
            else:
                # this title is not in the given location: check all other locations
                similar = [x for x in dbTitles if x['locations_ref'] != locationId \
                                           and (stringUtils.isSimilar(title, x['title']))
                          ]

                if len(similar) >= 1:
                    # found a similar title in a different location
                    self.logger.debug("Found title '%s', similar to '%s' already in the db " + \
                                      "but in a different location (%d): adding current location.", \
                                      title, similar[0]['title'], locationId)

                    cur.execute("INSERT INTO titles_in_locations (titles_ref, locations_ref) VALUES (?, ?);", \
                                (similar[0]['tid'], locationId))
                    newTitleInLocationId = cur.lastrowid
                    newTitleId = similar[0]['tid']

                else:
                    # Bona fide new title: insert the title for this location
                    self.logger.debug("Brand new title '%s', adding it to titles and to location %d.", \
                                      title, locationId)

                    cur.execute("INSERT INTO titles(title) VALUES (?);", (title,))
                    newTitleId = cur.lastrowid

                    # and then insert it in the TIL table
                    cur.execute("INSERT INTO titles_in_locations (titles_ref, locations_ref) VALUES (?, ?);", \
                                (newTitleId, locationId))
                    newTitleInLocationId = cur.lastrowid

            return (newTitleId, newTitleInLocationId)

    def insertShow(self, titlesRef = None, locationsRef = None, date = None):
        """Inserts a new show for the given titles(id) on the specified date.
        If the same (titles_ref , date) tuple is already there, this is a no-op.

        If date is None, then today's date is used.
        The format for the date string should be '%Y-%m-%d'.

        Returns the show primary key.
        """
        assert titlesRef != None, "Cannot insert a show with a null titlesRef!"
        assert isinstance(titlesRef, int), "Cannot insert a show with a titlesRef of type %s, should be an int!" % (type(titlesRef))
        assert locationsRef != None, "Cannot insert a show with a null locationsRef!"
        assert isinstance(locationsRef, int), "Cannot insert a show with a locationsRef of type %s, should be an int!" % (type(locationsRef))

        currDate = datetime.date.today().strftime('%Y-%m-%d')

        if date is None:
            date = currDate

        with (closing(db.cursor(self._conn))) as cur:
            cur.execute("SELECT id FROM titles_in_locations WHERE titles_ref = ? and locations_ref = ?;", (titlesRef, locationsRef))
            tilId = cur.fetchone()

            # if this title was not shown before in this location, add it to the titles_in_locations table
            if tilId is None:
                cur.execute("INSERT INTO titles_in_locations(titles_ref, locations_ref) VALUES (?, ?);", (titlesRef, locationsRef))
                tilId = cur.lastrowid
            else:
                tilId = tilId['id']

            # check if there has been already a show in this location for this date
            cur.execute("SELECT id FROM shows WHERE date = ? AND titles_in_locations_ref = ?;", (date, tilId))
            showId = cur.fetchone()

            if showId != None:
                # show was already recorded
                newId = showId['id']
            else:
                # new show: insert new record
                cur.execute("INSERT INTO shows(date, titles_in_locations_ref) VALUES (?, ?);", (date, tilId))
                newId = cur.lastrowid

            return newId

    def getAllTitlesInLocation(self, locationsId = None):
        """
        Given a locations Id, returns a list of dictionaries representing the titles.

        Output structure:
            [{'tid': title Id,
              'tilid': titles_in_locaitons id,
              'title': title string,
              'first_show': date of the first show of this title in this location,
              'last_show': date of the most recent show of this title in this location,
              'locations_ref': id of the location}]
        """
        with (closing(db.cursor(self._conn))) as cur:
            cur.execute("""SELECT t.id tid,
                                  t.title title,
                                  til.id tilid,
                                  min(s.date) first_show,
                                  max(s.date) last_Show,
                                  locations_ref
                           FROM titles t,
                                locations l,
                                titles_in_locations til,
                                shows s
                           WHERE t.id = til.titles_ref
                           AND s.titles_in_locations_ref = til.id
                           AND til.locations_ref = ?
                           GROUP BY t.id, t.title, til.id
                           ORDER BY t.title;
                        """, (locationsId,))

            rows = cur.fetchall()
            output = [{'tid': r['tid'], \
                       'tilid': r['tilid'], \
                       'title': r['title'], \
                       'first_show': r['first_show'], \
                       'last_show': r['last_show'], \
                       'locations_ref': r['locations_ref']} \
                      for r in rows]

        return output
