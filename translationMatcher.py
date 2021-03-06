"""
Created on Dec 29, 2018

@author: Guido

Module to reconcile the titles across different translations in the movieDiversity db.
"""
import logging
import argparse
from pprint import pformat

import movieLogger
import sources
import tmdb
from utils import stringUtils

class TranslationMatcher(object):
    """
    Module which will match a title with its translations in the db.
    """
    sources = None
    tmdbClient = None
    allTitles = None
    logger = None

    def __init__(self, dbfile = None):
        """
        Builds a local instance of the Sources class and
        one of the MovieLogger engine.
        """
        self.sources = sources.Sources(dbfile = dbfile)
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
        locations = self.sources.getAllLocations(False)
        for loc in locations:
            self.logger.info("Looking at %s." % (loc.name))

            titlesInLoc = self.sources.getNonTranslatedTitlesInLocation(loc.id)

            # for each title:
            for aTitleInLoc in titlesInLoc:

                # clean up the 3D, (OV), etc...
                aTitleInLoc['title'] = stringUtils.cleanupTitle(aTitleInLoc['title'])

                ####
                # LOCAL CHECKS:
                # verify if this title and language are already in, insert it if needed,
                # updates the stats accordingly
                check = self.cheeckLocallyAndInsertTitle(aTitleInLoc = aTitleInLoc, theLanguage = loc.language)
                if check == 0:
                    stats['existing'] += 1
                elif check == 1:
                    stats['new'] += 1

                ####
                # TMDB REMOTE CHECKS:
                # new title, look it up on imdb
                else:
                    check = self.checkTMBDAndInsertTitle(aTitleInLoc = aTitleInLoc, theLanguage = loc.language)
                    if check == 0:
                        stats['ambiguous'] += 1
                    elif check == 1:
                        stats['new'] += 1
                    elif check == -1:
                        stats['not found'] += 1

        self.logger.info("End run:\n\t{new:5} new translations\n\t{existing:5} existing\n\t{ambiguous:5} ambiguous\n\t{not found:5} not found"
                        .format_map(stats))

    def cheeckLocallyAndInsertTitle(self, aTitleInLoc = None, theLanguage = None):
        """
        Check if the title was already translated in the current db and if it was already
        here but with a different language, inserts it in.
        Returns:
            +1 if this is a new translation of an existing title
             0 if this translation was already in,
            -1 if this title was not found in the local db
        """
        output = -1
        knownTranslations = self.sources.getAllTranslationsAlreadyIn(aTitleInLoc['tid'],
                                                                     aTitleInLoc['language'])
        if len(knownTranslations) > 0:
            if len(knownTranslations) == 1:
                # translation already there: move on
                self.logger.info("Translation of \"%s\" in %s already in (%s)" % (aTitleInLoc['title'], aTitleInLoc['language'], knownTranslations[0]['tmdb_id']))
                output = 0

            else:
                # there are translation from other languages already in:
                # add this translation without asking tmdb
                self.logger.info("Adding %s translation for \"%s\" to the table" % (aTitleInLoc['language'], aTitleInLoc['title']))
                self.insertTranslation(titleRec = aTitleInLoc, \
                               titleLanguage = theLanguage, \
                               tmdbId = knownTranslations[0]['tmdb_id'],
                               originalTitle = knownTranslations[0]['original_title'],
                               originalLanguage = knownTranslations[0]['original_language'])
                output = 1

        return output

    def checkTMBDAndInsertTitle(self, aTitleInLoc = None, theLanguage = None):
        """
        Check if the title has a unique translation found in TIMDB, if so inserts it
        Returns:
            -1 if this translation is not found in TIMDB at all (no insert performed)
             0 if this title has ambiguous translations (more than one fits, no inserts)
            +1 if this title has one unique translation in TIMDB and has been inserted
        """

        # get the info from tmdb
        movieRec = self.tmdbClient.searchByTitle(aTitleInLoc['title'], theLanguage)
        self.logger.debug("Got %d titles for %s" % (len(movieRec['results']), aTitleInLoc['title']))

        # check the translations returned
        if len(movieRec['results']) == 0:
            # unknown title just log it
            self.logger.warn("No results found at all for \"%s\" in %s!" % (aTitleInLoc['title'], theLanguage))
            output = -1

        elif len(movieRec['results']) == 1:
            # match found
            self.insertTranslation(titleRec = aTitleInLoc, \
                                   titleLanguage = theLanguage, \
                                   tmdbId = movieRec['results'][0]['id'],
                                   originalTitle = movieRec['results'][0]['original_title'],
                                   originalLanguage = movieRec['results'][0]['original_language'])
            output = 1

        else:
            # several translations found: how many with the exact same title?
            exactMatch = [rec for rec in movieRec['results'] if rec['title'].lower() == aTitleInLoc['title'].lower()]

            if len(exactMatch) == 0:
                # ambiguous results: no exact one - log and move on
                self.logger.warn("Too many matches for \"%s\" and no exact match at all (found %d matches)" % (aTitleInLoc['title'], len(movieRec['results'])))
                output = 0

            elif len(exactMatch) > 1:
                # several exact match: anyone in the same language?
                exactMatchWithLang = [rec for rec in exactMatch if rec['title'].lower() == aTitleInLoc['title'].lower() and rec['original_language'] == aTitleInLoc['language']]

                if len(exactMatchWithLang) == 1:
                    # match found
                    self.insertTranslation(titleRec = aTitleInLoc, \
                                           titleLanguage = theLanguage, \
                                           tmdbId = movieRec['results'][0]['id'],
                                           originalTitle = exactMatchWithLang[0]['original_title'],
                                           originalLanguage = exactMatchWithLang[0]['original_language'])
                    output = 1
                else:
                    # totally ambiguous match: too many exact matches - log and move on
                    for r in exactMatch:
                        if "release_date" not in r.keys():
                            r['release_date'] = ''
                    self.logger.warning("Too many exact matches: ambiguous title (%s) yielded:\n%s" % \
                                    (aTitleInLoc['title'], pformat([(t['title'], t['original_language'], t['release_date']) for t in exactMatch])))
                    output = 0

            else:
                # unique exact match: match found
                self.insertTranslation(titleRec = aTitleInLoc, \
                                       titleLanguage = theLanguage, \
                                       tmdbId = movieRec['results'][0]['id'],
                                       originalTitle = exactMatch[0]['original_title'],
                                       originalLanguage = exactMatch[0]['original_language'])
                output = 1

        return output

    def insertTranslation(self, originalTitle, originalLanguage, titleRec, titleLanguage, tmdbId):
        """
        Records the title from titleRec as a translation of the movie 
        with id = tmdbId in TMDB for the language titleLanguage. 
        """
        self.logger.info("Title \"%s\" in %s was originally \"%s\" in %s (%s)" % (titleRec['title'], titleLanguage, originalTitle, originalLanguage, tmdbId))
        self.sources.insertTranslation(titlesRef = titleRec['tid'], lang_from = titleLanguage, tmdb_id = tmdbId)

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

