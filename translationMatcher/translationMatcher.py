"""
Created on Dec 29, 2018

@author: Guido

Module to reconcile the titles across different translations in the movieDiversity db.
"""
import logging
import argparse
from pprint import pformat

import movieLogger
import sourcesAlchemy
import tmdb
from utils import stringUtils
from sqlalchemy.testing.util import fail

class TranslationMatcher(object):
    """
    Module which will match a title with its translations in the db.
    """
    source = None
    tmdbClient = None
    allTitles = None
    logger = None

    def __init__(self, dbfile = None):
        """
        Builds a local instance of the Sources class and
        one of the MovieLogger engine.
        """
        self.source = sourcesAlchemy.SourcesAlchemy(dbfile = dbfile)
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        self.tmdbClient = tmdb.tmdbRestClient()

        self.logger.info("TranslationMatcher instance inited.")

    def reconcileAllTitles(self):
        # build a list/map of all titles and their location
        locations = self.source.getAllLocations(False)
        for loc in locations:

############
#           DEBUG
            if loc.name != "Milano":
                continue
#
############

            titlesInLoc = self.source.getAllTitlesInLocation(loc.id)
            self.logger.info("Found %d titles in %s." % (len(titlesInLoc), loc.name))

            # for each title:
            for aTitleInLoc in titlesInLoc:

                # clean up the 3D, (OV), etc...
                aTitleInLoc['title'] = stringUtils.cleanupTitle(aTitleInLoc['title'])

                # look it up on imdb
                movieRec = self.tmdbClient.searchByTitle(aTitleInLoc['title'], loc.language)
                self.logger.debug("Got %d titles for %s" % (len(movieRec['results']), aTitleInLoc['title']))

                # check if the translation returned is != from original title
                if len(movieRec['results']) == 0:
                    self.logger.error("No results found at all for %s\" in %s!" % (aTitleInLoc['title'], loc.language))

                elif len(movieRec['results']) == 1:
                    self.logger.info("Title \"%s\" in %s was originally \"%s\" in %s" % (aTitleInLoc['title'], loc.language, movieRec['results'][0]['original_title'], movieRec['results'][0]['original_language']))
#                     self.insertTranslation(titleRec = aTitleInLoc, \
#                                            titleLanguage = loc.language, \
#                                            tmdbId = movieRec['results'][0]['id'])

                else:
                    exactMatch = [rec for rec in movieRec['results'] if rec['title'].lower() == aTitleInLoc['title'].lower()]
                    if len(exactMatch) == 0:
                        self.logger.error("Too many matches for \"%s\" and no exact match at all (found %d matches)" % (aTitleInLoc['title'], len(movieRec['results'])))
                    elif len(exactMatch) > 1:
                        self.logger.warning("Too many exact matches: ambiguous title (%s) yielded:\n%s" % \
                                            (aTitleInLoc['title'], pformat([(t['title'], t['original_language']) for t in exactMatch])))
                    else:
                        self.logger.info("Title \"%s\" in %s was originally \"%s\" in %s" % (aTitleInLoc['title'], loc.language, exactMatch[0]['original_title'], exactMatch[0]['original_language']))

        #    find if there was a match, insert into the translation table

    def insertTranslation(self, titleRec, titleLanguage, tmdbId):
        """
        Records the title from titleRec as a translation of the movie 
        with id = tmdbId in TMDB for the language titleLanguage. 
        """
        fail

# ##
#
# main entry point
#
# ##
if __name__ == '__main__':
    # Parse arguments from command line
    parser = argparse.ArgumentParser(description = 'TranslationMatcher is a python app to ' +
                                     'reconcile different translations of the same movie in ' +
                                     'a MovieDiversity db.')
    parser.add_argument('--dbfile', '-db',
                        required = True,
                        help = 'The sqlite db file to be used.')
    parser.add_argument('--logLevel', '-log',
                        required = False,
                        choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help = 'The level of output for logging. Defaults to INFO.')

    args = parser.parse_args()

    # Init the logging system
    movieLogger.MovieLoggger().initLogger(level = args.logLevel)

    T = TranslationMatcher(dbfile = args.dbfile)

    T.logger.info("Populating translation table in : %s", args.dbfile)

    T.reconcileAllTitles()

    T.logger.info("End run.")

