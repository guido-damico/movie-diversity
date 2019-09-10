'''
Created on March 3, 2019

@author: Guido

Source module for the MovieDiversity app.
'''
from pprint import pformat
import logging
import datetime

import movieLogger
import tests.utils
from utils import stringUtils

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import func

import movieDbClasses
from movieDbClasses import Locations
from movieDbClasses import Sites
from movieDbClasses import Titles
from movieDbClasses import TitlesInLocations
from movieDbClasses import Shows
from movieDbClasses import Translations

class SourcesAlchemy(object):
    """
        This class exposes commodity methods to query the db and get structured data back.
        It uses internally SQLAlchemy, but it hides all the SQLAlchemy's classes from the user,
        all methods return plan dictionaries, hiding the db implementation from the callers.
        
        It depends on movieLogger.MovieLogger.
    """

    logger = None
    _conn = None

    # locally cached data containers
    _locations = []
    _sites = []

    # sqlite db file
    _dbName = '/home/guido/work/git/movie-diversity/movieDiversity.db'
    _dbConnectString = 'sqlite:///'

    # classes to be used by SQLAlchemy for query and manipulation
    locationClass = None
    sitesClass = None
    titlesClass = None
    titlesInLocationsClass = None
    showsClass = None

    # auto-commit?
    # _isolationLevel = None

    def __init__(self, dbfile = _dbName):
        """
            Gets a local copy of the logger.
            Connects to the sqlite data db specified by "dbfile" and
            verifies that the schema is clean.
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        # Create the SQLAlchemy connection
        self._dbConnectString = self._dbConnectString + dbfile
        dbEngine = create_engine(self._dbConnectString)

        # Enforce FK constraints
        def _enforceFKContraintsOnConnect(dbapi_conn, con_record):
            dbapi_conn.execute('PRAGMA foreign_keys=ON')

        event.listen(dbEngine, 'connect', _enforceFKContraintsOnConnect)

        movieDbClasses.Base.metadata.bind = dbEngine
        DBSession = sessionmaker()
        DBSession.bind = dbEngine
        self.session = DBSession()

        # store copy of the db wrapper classes
        self.locationClass = getattr(movieDbClasses, "Locations")
        self.sitesClass = getattr(movieDbClasses, "Sites")
        self.titlesClass = getattr(movieDbClasses, "Titles")
        self.titlesInLocationsClass = getattr(movieDbClasses, "TitlesInLocations")
        self.showsClass = getattr(movieDbClasses, "Shows")
        self.translationClass = getattr(movieDbClasses, "Translations")

        self.logger.debug("Created wrapper classes container instances")

        # for direct SQL manipulation of the db: have the util class inited correctly
        # and check for data cleanliness
        self.util = tests.utils.Utils(dbfile = self._dbName,
                                      logger = self.logger)
        self.util.checkDbDataTestNames()

    def getAllLocations(self,
                        refresh = False):
        """
        Returns all the locations known to the class up to this point.
        Return type is a list of Locations class instances.

        If "Refresh" is set to True, or if there are not locations in the cache,
        performs a new query to the db to get fresh data.
        """
        if refresh or len(self._locations) == 0:

            # query
            rec = self.session.query(self.locationClass).all()
            self.logger.debug("Queried db for locations")

            self._locations = rec

        return self._locations

    def getLocationSitesData(self,
                             locationName = "",
                             refresh = False):
        """
        Given a location name, it returns all the currently known data for that
        location, in the form of a list of dictionaries.

        If "Refresh" is set to True, or if there is no data in the cache,
        performs a new query to the db to get fresh data.

        The data returned is in the form of a list of dictionaries with the
        information about the URL, title_xpath, and Active status of the sites
        connected to the given location.
        """
        if refresh or len(self._sites) == 0:
            self.logger.debug("Refreshing data for locations and their sites.")

            # get all sites and their locations
            allData = self.session.query(self.locationClass, self.sitesClass) \
                                .filter(Sites.locations_ref == Locations.id) \
                                .all()
            self.logger.debug("Queried db for join locations and sites")

            # Build the dictionary in output
            for rec in allData:
                self._sites.append({'id': rec.Sites.id,
                                    'name': rec.Sites.name,
                                    'url': rec.Sites.url,
                                    'title_xpath': rec.Sites.title_xpath,
                                    'active': rec.Sites.active,
                                    'locations_ref': rec.Sites.locations_ref,
                                    'location_name': rec.Locations.name})

        return [x for x in self._sites if x['location_name'] == locationName]

    def getAllTitles(self):
        """
        Returns a list of titles in the db.
        """
        # query
        recs = self.session.query(self.titlesClass).all()
        self.logger.debug("Queried db for titles")

        return recs

    def getAllTitlesAndLocations(self):
        """
        Returns a list of dictionaries with titles is and their locations_ref.
        """
        # query
        recs = self.session.query(self.titlesClass, self.locationClass, self.titlesInLocationsClass) \
                           .filter(Titles.id == TitlesInLocations.titles_ref) \
                           .filter(TitlesInLocations.locations_ref == Locations.id) \
                           .all()
        self.logger.debug("Queried db for titles")

        output = []

        # Build the dictionary in output
        for rec in recs:
            output.append({'id': rec.Titles.id,
                           'title': rec.Titles.title,
                           'locations_ref': rec.Locations.id,
                           'tilid': rec.TitlesInLocations.id})

        return output

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
        output = []

        # query
        recs = self.session.query(self.titlesClass.id.label("titles_id"), \
                                  self.titlesClass.title, \
                                  self.locationClass.id.label("locations_id"), \
                                  self.locationClass.language.label("language"), \
                                  self.titlesInLocationsClass.id.label("titles_in_locations_id"), \
                                  func.min(self.showsClass.date).label("first_show"), \
                                  func.max(self.showsClass.date).label("last_show")) \
                           .filter(Titles.id == TitlesInLocations.titles_ref) \
                           .filter(TitlesInLocations.locations_ref == Locations.id) \
                           .filter(TitlesInLocations.locations_ref == locationsId) \
                           .filter(Shows.titles_in_locations_ref == TitlesInLocations.id) \
                           .group_by(Titles.id) \
                           .group_by(TitlesInLocations.id) \
                           .order_by(Titles.title) \
                           .all()

        # Build the dictionary in output
        self.logger.debug("Got: %d titles" % len(recs))
        output = [{'tid': rec.titles_id, \
                   'tilid': rec.titles_in_locations_id, \
                   'title': rec.title, \
                   'first_show': rec.first_show, \
                   'last_show': rec.last_show, \
                   'locations_ref': rec.locations_id, \
                   'language': rec.language} \
                  for rec in recs]

        return output

    def insertTitleInLocation(self, aTitle = None, locationId = None):
        """
        Inserts a new title for the given location in the db.
        If the same title exists, but in a different location, a new
        record is created in titles_in_locations linking the existing title
        with the new location.

        If the same title exists in the given location, this is a no-op.

        Returns the titles_in_locations record primary key (id).
        """

        newTitleId = None
        newTitleInLocationId = None

        assert aTitle != None and aTitle != "", \
            "Attempted to insert a NULL title!"
        assert locationId != None and isinstance(locationId, int), \
            "Attempted to insert a title with an invalid location (%s)!" % locationId

        dbTitles = self.getAllTitlesAndLocations()
        # check whether the title is similar to one already in for this location
        similar = [x for x in dbTitles if x['locations_ref'] == locationId \
                                        and (stringUtils.isSimilar(aTitle, x['title']))
                  ]

        if len(similar) == 1:
            # found a similar title already in
            self.logger.debug("Found title '%s', similar to '%s' already in the db: using db version.", \
                             aTitle, similar[0]['title'])
            newTitleId = similar[0]['id']
            newTitleInLocationId = similar[0]['tilid']

        elif len(similar) > 1:
            # data inconsistency! Found many similar titles, can't proceed: log an error and discard this record
            self.logger.error("Cannot insert title '%s', found too many similar ones already in the db:\n%s", aTitle, pformat(similar))

        else:
            # this title is not in the given location: check all other locations
            similar = [x for x in dbTitles if x['locations_ref'] != locationId \
                                      and (stringUtils.isSimilar(aTitle, x['title']))
                      ]
            if len(similar) >= 1:
                # found a similar title in a different location
                self.logger.debug("Found title '%s', similar to '%s' already in the db " + \
                                 "but in a different location (%d): adding current location.", \
                                 aTitle, similar[0]['title'], locationId)
                newTitleInLocation = TitlesInLocations(titles_ref = similar[0]['id'], locations_ref = locationId)
                self.session.add(newTitleInLocation)
                newTitleInLocationId = self.session.commit()
                newTitleInLocationId = newTitleInLocation.id
                newTitleId = similar[0]['id']
            else:
                # Bona fide new title: insert the title for this location
                self.logger.debug("Brand new title '%s', adding it to titles and to location %d.", \
                                 aTitle, locationId)
                titleRec = self.titlesClass(title = aTitle)
                self.session.add(titleRec)
                self.session.commit()
                newTitleId = titleRec.id

                # and then insert it in the TIL table
                titleInLocRec = self.titlesInLocationsClass(titles_ref = newTitleId, locations_ref = locationId)
                self.session.add(titleInLocRec)
                self.session.commit()
                newTitleInLocationId = titleInLocRec.id

        return (newTitleId, newTitleInLocationId)

    def insertShow(self, titlesRef = None, locationsRef = None, date = None):
        """
        Inserts a new show for the given titles(id) on the specified date.
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

        # find this title in this location
        titleInLoc_recs = self.session.query(self.titlesInLocationsClass) \
                         .filter(TitlesInLocations.titles_ref == titlesRef) \
                         .filter(TitlesInLocations.locations_ref == locationsRef) \
                         .all()

        # if this title was not shown before in this location, add it to the titles_in_locations table
        if len(titleInLoc_recs) == 0:
            newTitleInLocation = TitlesInLocations(titles_ref = titlesRef, locations_ref = locationsRef)
            self.session.add(newTitleInLocation)
            newTitleInLocationId = self.session.commit()
            newTitleInLocationId = newTitleInLocation.id
        else:
            newTitleInLocationId = titleInLoc_recs[0].id

        # check if there has been already a show in this location for this date
        shows_recs = self.session.query(self.showsClass) \
                    .filter(Shows.date == date) \
                    .filter(Shows.titles_in_locations_ref == newTitleInLocationId) \
                    .all()

        # if there was one, record it, if not insert it on today's date
        if len(shows_recs) == 0:
            newShow = Shows(date = date, titles_in_locations_ref = newTitleInLocationId)
            self.session.add(newShow)
            newShowId = self.session.commit()
            newShowId = newShow.id
        else:
            newShowId = shows_recs[0].id

        return newShowId

    def getAllTranslationsAlreadyIn(self, titlesRef = None, lang_from = None):
        """
            Returns all the translations for this title already in the table. 
        """
        # find any other translation for this title
        translation_recs = self.session.query(self.translationClass) \
                         .filter(Translations.title_from_ref == titlesRef) \
                         .all()

        # if there is a record with exactly the same translation, return just that one
        if lang_from in set([x.lang_from for x in translation_recs]):
            translation_recs = [x for x in translation_recs if x.lang_from == lang_from]

        # Build the dictionary in output
        output = [{'id': rec.id, \
                   'title_from_ref': rec.title_from_ref, \
                   'lang_from': rec.lang_from, \
                   'tmdb_id': rec.tmdb_id} \
                  for rec in translation_recs]

        return output

    def insertTranslation(self, titlesRef = None, lang_from = None, tmdb_id = None):
        """
        Links a new translation for the given title_ref in the specified language for the movie with that tmdb_id.
        If the same (titles_ref , lang, tmdb_d) tuple is already there, this is a no-op.

        If date is None, then today's date is used.
        The format for the date string should be '%Y-%m-%d'.

        Returns the show primary key.
        """
        assert titlesRef != None, "Cannot insert a translation with a null titlesRef!"
        assert isinstance(titlesRef, int), "Cannot insert a translation with a titlesRef of type %s, should be an int!" % (type(titlesRef))
        assert tmdb_id != None, "Cannot insert a show with a null tmdb id"
        assert isinstance(tmdb_id, int), "Cannot insert a show with a tmdb id of type %s, should be an int!" % (type(tmdb_id))

        # decision flag
        addTranslation = False

        # return value
        newTranslationId = None

        # get any other translation for this title
        translation_recs = self.getAllTranslationsAlreadyIn(titlesRef, lang_from)

        if len(translation_recs) == 0:
            # brand new translation
            addTranslation = True

        else:
            # one or more translations here already: look for the same language
            sameLanguage = [x for x in translation_recs if x['lang_from'] == lang_from]

            if len(sameLanguage) == 0:
                # new translation for a known title: add it
                addTranslation = True

            elif len(sameLanguage) == 1:
                # translation was already in: return it
                newTranslationId = sameLanguage[0]['id']

        if addTranslation:
            newTranslation = Translations(title_from_ref = titlesRef, lang_from = lang_from, tmdb_id = tmdb_id)
            self.session.add(newTranslation)
            newTranslationId = self.session.commit()
            newTranslationId = newTranslation.id

        return newTranslationId

    def rollbackSession(self):
        """
        In case of an exception during a transaction, the user needs to be able to clean up the session,
        by rolling it back before being able to initiate another one.
        """
        self.session.rollback()
