'''
Created on May 5, 2017

@author: Guido

Main package to perform the MovieDiversity data collection.
'''
from lxml import html
import requests
import sqlite3
import logging, movieLogger

class Scraper(object):
    """
        Scraper implementation class.
        
        Implements the Movie data collection functions and depends on
        the Sources and movieLogger.MovieLogger classes.
    """
    _source = None
    _logger = None
    similarityThreshold = 0.5
    
    def __init__(self):
        """Builds a local instance of the Sources class and
        one of the MovieLogger engine.
        """
        self._source = Sources()
        self._logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

    def getMoviesTitles(self, location=""):
        """Given the sting name of a location, it returns a
        set of all movie titles playing there today.
        """
        output = frozenset([])

        data = self._source.getLocationData(location)
        for site in data:
            if site['active']:
                output = output.union(self.getMoviesTitlesFromData(url = site['url'], title_xpath = site['title_xpath']))

        return self.cleanupTitles(output)
        
    def getMoviesTitlesFromData(self, url="", title_xpath=""):
        """Given a URL an an xpath query to identify the titles of the movies on the
        page returned by the URL, it returns a set of all the titles.
        """
        page = requests.get(url)
        tree = html.fromstring(page.content)
        output = frozenset(tree.xpath(title_xpath))
        return output
    
    def isSimilar(self, title1 = "", title2 = ""):
        """Given two strings, it returns True if their
        similarity is closer than Scraper.similarityThreshold
        """
        title1 = "".join(title1.split())
        title2 = "".join(title2.split())
        len1 = len(title1)
        len2 = len(title2)
        same = [x for x in range(0, min(len1, len2)) if title1[x] == title2[x]]

        ratio = len(same) / max(len1, len2)

        self._logger.debug("Similarity between '%s' and '%s' is %.3f", title1, title2, ratio)
        return ratio > self.similarityThreshold

    def cleanupTitles(self, titles = None):
        """Given a set of strings, it de-duplicates the ones
        which are similar enough.
        For instance "Star Wars: a new hope" and "Star Wars - A New Hope"
        should be deemed similar and reported only once.
        """
        assert isinstance(titles, frozenset)
        assert len(titles) > 0
        
        titlesList = [x.replace("\n", " ") for x in titles]

        output = frozenset([])
        similar = frozenset([])
        
        for ptr in range(0, len(titlesList)):
            for cmp in range(ptr + 1, len(titlesList)):
                if self.isSimilar(titlesList[ptr], titlesList[cmp]):
                    similar = similar.union([titlesList[cmp]])
        output = titles.difference(similar)
        
        return output

class Sources(object):
    """
        Implementation of the sources to be used with Scraper.
        All db-level actions (towards sqlite) are defined here.
        
        It depends on movieLogger.MovieLogger. 
    """

    _logger = None
    _conn = None
    _locations = []
    _data = []
    
    _sqliteFileName = '/home/guido/work/git/movie-diversity/movieDiversity.db'
    _schemaData = {
                'locations':
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
                     "name text",
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
    
    def __init__(self):
        """
            Gets a local copy of the logger.
            Connects to the sqlite data db and verifies that the schema has been
            defined correctly.
            
            The MovieDiversity.sql file contains a valid seeding of the db.
        """
        self._logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)
        self._conn = sqlite3.connect(self._sqliteFileName)
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.cursor()
        
        self._logger.info("Verifying db schema tables...")
        cur.execute("SELECT lower(sql) FROM sqlite_master;")
        allTables = cur.fetchall()
        try:
            assert len(allTables) == 5, "movieDiversity.db file should have 5 tables defined (found %d)." % len(allTables)
            
            self._verifyFormat(allTables, self._schemaData)
            
        except AssertionError as ae:
                raise AssertionError("Failed db schema validation: execution will stop.\n" + ae.__str__()) 
                    
    def _verifyFormat(self, statements = [], schemaData = []):
        """Verifies that the definitions of the db schema conforms to the
        expectations of this class.
        """
        tablesNames = schemaData.keys()
        for t in tablesNames:
            stmt = [x[0] for x in statements if "create table " + t in x[0]]

            self._logger.debug("Verifying creating table %s", t)            
            assert len(stmt) == 1 and ("create table %s" % t) in stmt[0], "Table %s not found in schema." % t
            
            for c in schemaData[t]:
                self._logger.debug("Verifying column %s in table %s", c, t)            
                assert c in stmt[0], \
                    "Declaration for '%s' not found in table %s.\n schD = %s\nstmt = %s" % (c, t, schemaData[t], stmt[0])
        self._logger.info("Verification terminated and passed.")

    def getAllLocations(self,
                        refresh = False):
        """Returns all the locations known to the class up to this point.
        If "Refresh" is set to True, performs a new query to the db to get
        fresh data.
        """
        if refresh or len(self._locations) == 0:
            cur = self._conn.cursor()
            cur.execute('SELECT name FROM locations;')
            self._locations = cur.fetchall()
            self._locations = [x[0] for x in self._locations]

        return self._locations
        
        return allLocations
    
    def getLocationData(self,
                        location = "",
                        refresh = False):
        """Given a location, it returns all the currently known data for that
        location.
        If "Refresh" is set to True, performs a new query to the db to get
        fresh data.
        
        The data returns is in the form of a list of dictionaries with the
        information about the URL, title_xpath, and Active status of the sites
        connected to the given location.
        """
        if refresh or len(self._data) == 0:
            allLocations = self.getAllLocations()

            cur = self._conn.cursor()
            cur.execute('SELECT s.id, s.name, url, title_xpath, active, l.name location_name ' + \
                        'FROM locations l, sites s ' + \
                        'WHERE  s.locations_ref = l.id;')
            allData = cur.fetchall()

            for r in allData:
                self._data.append({k: r[k] for k in r.keys()}) 

        return [x for x in self._data if x['location_name'] == location] 
    
if __name__ == "__main__":
    from pprint import pprint, pformat
    movieLogger.MovieLoggger().initLogger()

    S = Scraper()
    
    allLocations = S._source.getAllLocations()
    S._logger.info("All locations: %s", allLocations)

    output = S.getMoviesTitles("San Francisco")
    S._logger.info("SAN FRANCISCO - Got %d movies:" %(len(output)))
    S._logger.info(pformat(output))

    output = S.getMoviesTitles("Milano")
    S._logger.info("MILANO - Got %d movies:" %(len(output)))
    S._logger.info(pformat(output))
