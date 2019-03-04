'''
Created on March 3, 2019

@author: Guido

Source module for the MovieDiversity app.
'''
from pprint import pformat
import logging
import movieLogger
import tests.utils

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import movieDbClasses
from movieDbClasses import Locations
from movieDbClasses import Sites
from movieDbClasses import Titles
from movieDbClasses import TitlesInLocations
from movieDbClasses import Shows
from movieDbClasses import Translations

class SourcesAlchemy(object):
    """
        Implementation of the sources data with SQLAlchemy, to be used by Scraper.
        All db-level actions (towards sqlite) are defined here.

        It depends on movieLogger.MovieLogger.
    """

    logger = None
    _conn = None
    _locations = []
    _data = []

    # sqlite db location
    _dbName = '/home/guido/work/git/movie-diversity/movieDiversity.db'
    _dbConnectString = 'sqlite:///' + _dbName

    # auto-commit?
    _isolationLevel = None

    def __init__(self, dbfile = _dbName):
        """
            Gets a local copy of the logger.
            Connects to the sqlite data db specified by "dbfile" and
            verifies that the schema has been defined correctly.

            The MovieDiversity.sql file contains a valid seeding of the db.
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        dbEngine = create_engine(self._dbConnectString)
        movieDbClasses.Base.metadata.bind = dbEngine
        DBSession = sessionmaker()
        DBSession.bind = dbEngine
        self.session = DBSession()

        self.util = tests.utils.Utils(dbfile = self._dbName,
                                      logger = self.logger)

        self.util.checkDbDataTestNames()

    def getAllLocations(self,
                        refresh = False):
        """
        Returns all the locations known to the class up to this point.
        If "Refresh" is set to True, or if there are not locations in the cache,
        performs a new query to the db to get fresh data.
        """
        if refresh or len(self._locations) == 0:

            # create an instance of the container class
            locationsCls = getattr(movieDbClasses, "Locations")
            self.logger.debug("Created location container instance")
            # query
            rec = self.session.query(locationsCls).all()
            self.logger.debug("Queried db")

            self._locations = rec

        return self._locations
