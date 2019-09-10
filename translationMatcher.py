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
        """
            Browse all the titles and find their translations.
        """
        # stats container
        stats = {
                 'new': 0,
                 'existing': 0,
                 'ambiguous': 0,
                 'not found': 0
                }

        # build a list/map of all titles and their location
        locations = self.source.getAllLocations(False)
        for loc in locations:

############
#           DEBUG
            if loc.name != "Cairo":
                continue
#
############

            titlesInLoc = self.source.getAllTitlesInLocation(loc.id)
            self.logger.info("Found %d titles in %s." % (len(titlesInLoc), loc.name))

            # for each title:
            for aTitleInLoc in titlesInLoc:

                # clean up the 3D, (OV), etc...
                aTitleInLoc['title'] = stringUtils.cleanupTitle(aTitleInLoc['title'])

                ####
                # LOCAL CHECKS:
                # verify if this title and language are already in
                knownTranslations = self.source.getAllTranslationsAlreadyIn(aTitleInLoc['tid'],
                                                                            aTitleInLoc['language'])
                if len(knownTranslations) > 0:
                    if len(knownTranslations) == 1:
                        # translation already there: move on
                        self.logger.info("Already one %s translation for \"%s\": %s" % (aTitleInLoc['language'], aTitleInLoc['title'], knownTranslations[0]['tmdb_id']))
                        stats['existing'] += 1
                        continue

                    else:
                        # there are translation from other languages already in:
                        # add this translation without asking tmdb
                        self.logger.info("Adding %s translation for \"%s\" to the table" % (aTitleInLoc['language'], aTitleInLoc['title']))
                        self.insertTranslation(titleRec = aTitleInLoc, \
                                               titleLanguage = loc.language, \
                                               tmdbId = knownTranslations[0]['tmdb_id'],
                                               originalTitle = knownTranslations[0]['original_title'],
                                               originalLanguage = knownTranslations[0]['original_language'])
                        stats['new'] += 1

                ####
                # TMDB REMOTE CHECKS:
                # new title, look it up on imdb
                else:

                    # get the info from tmdb
                    movieRec = self.tmdbClient.searchByTitle(aTitleInLoc['title'], loc.language)
                    self.logger.debug("Got %d titles for %s" % (len(movieRec['results']), aTitleInLoc['title']))

                    # check the translations returned
                    if len(movieRec['results']) == 0:
                        # unknown title - log and move on
                        self.logger.warn("No results found at all for \"%s\" in %s!" % (aTitleInLoc['title'], loc.language))
                        stats['not found'] += 1

                    elif len(movieRec['results']) == 1:
                        # match found
                        self.insertTranslation(titleRec = aTitleInLoc, \
                                               titleLanguage = loc.language, \
                                               tmdbId = movieRec['results'][0]['id'],
                                               originalTitle = movieRec['results'][0]['original_title'],
                                               originalLanguage = movieRec['results'][0]['original_language'])
                        stats['new'] += 1

                    else:
                        # several translations found: how many with the exact same title?
                        exactMatch = [rec for rec in movieRec['results'] if rec['title'].lower() == aTitleInLoc['title'].lower()]

                        if len(exactMatch) == 0:
                            # ambiguous results: no exact one - log and move on
                            self.logger.warn("Too many matches for \"%s\" and no exact match at all (found %d matches)" % (aTitleInLoc['title'], len(movieRec['results'])))
                            stats['ambiguous'] += 1

                        elif len(exactMatch) > 1:
                            # several exact match: anyone in the same language?
                            exactMatchWithLang = [rec for rec in exactMatch if rec['title'].lower() == aTitleInLoc['title'].lower() and rec['original_language'] == aTitleInLoc['language']]

                            if len(exactMatchWithLang) == 1:
                                # match found
                                self.insertTranslation(titleRec = aTitleInLoc, \
                                                       titleLanguage = loc.language, \
                                                       tmdbId = movieRec['results'][0]['id'],
                                                       originalTitle = exactMatchWithLang[0]['original_title'],
                                                       originalLanguage = exactMatchWithLang[0]['original_language'])
                                stats['new'] += 1
                            else:
                                # totally ambiguous match: too many exact matches - log and move on
                                self.logger.warning("Too many exact matches: ambiguous title (%s) yielded:\n%s" % \
                                                (aTitleInLoc['title'], pformat([(t['title'], t['original_language']) for t in exactMatch])))
                                stats['ambiguous'] += 1

                        else:
                            # unique exact match: match found
                            self.insertTranslation(titleRec = aTitleInLoc, \
                                                   titleLanguage = loc.language, \
                                                   tmdbId = movieRec['results'][0]['id'],
                                                   originalTitle = exactMatch[0]['original_title'],
                                                   originalLanguage = exactMatch[0]['original_language'])
                            stats['new'] += 1
                            self.logger.info("Title \"%s\" in %s was originally \"%s\" in %s" % (aTitleInLoc['title'], loc.language, exactMatch[0]['original_title'], exactMatch[0]['original_language']))

        self.logger.info("End run:\n\t%04d new translations\n\t%04d existing\n\t%04d ambiguous\n\t%04d not found")

    def insertTranslation(self, originalTitle, originalLanguage, titleRec, titleLanguage, tmdbId):
        """
        Records the title from titleRec as a translation of the movie 
        with id = tmdbId in TMDB for the language titleLanguage. 
        """
        self.logger.info("Title \"%s\" in %s was originally \"%s\" in %s (%s)" % (titleRec['title'], titleLanguage, originalTitle, originalLanguage, tmdbId))
        self.source.insertTranslation(titlesRef = titleRec['tid'], lang_from = titleLanguage, tmdb_id = tmdbId)

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

