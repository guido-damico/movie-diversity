'''
Created on May 5, 2017

@author: Guido

Main module to perform the MovieDiversity data collection app.
'''
import logging
import argparse
from pprint import pformat
import requests
from lxml import html
import sources
import movieLogger


def getMoviesTitlesFromData(url="", title_xpath=""):
    """Function which given a URL an an xpath query to identify the titles of the movies on the
    page returned by the URL, it returns a set of all the titles.
    """
    page = requests.get(url)
    tree = html.fromstring(page.content)
    titles = frozenset(tree.xpath(title_xpath))
    return titles


class Scraper(object):
    """
        Scraper implementation class.

        Implements the Movie data collection functions and depends on
        the Sources and movieLogger.MovieLogger classes.
    """
    _source = None
    logger = None
    similarityThreshold = 0.5

    def __init__(self, dbfile = None):
        """Builds a local instance of the Sources class and
        one of the MovieLogger engine.
        """
        self._source = sources.Sources(dbfile = dbfile)
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        self.logger.debug("Scraper instance inited.")

    def getMoviesTitles(self, location=""):
        """Given the sting name of a location, it returns a
        set of all movie titles playing there today.
        """
        self.logger.debug("Looking for movie titles in %s.", location)
        titles = frozenset([])

        data = self._source.getLocationData(location)
        # for every active site in the list, get the titles and insert them in the output set
        for site in data:
            if site['active']:
                titles = titles.union(getMoviesTitlesFromData(url = site['url'],
                                                              title_xpath = site['title_xpath']))

        # clean up before sending back
        return self.cleanupTitles(titles)

    def isSimilar(self, title1 = "", title2 = ""):
        """Given two strings, it returns True if their
        similarity is closer than Scraper.similarityThreshold
        """
        # first, eliminate all whitespaces
        title1 = "".join(title1.split())
        title2 = "".join(title2.split())

        # then count the letters which are the same
        len1 = len(title1)
        len2 = len(title2)
        same = [x for x in range(0, min(len1, len2)) if title1[x] == title2[x]]

        # similarity ratio
        ratio = len(same) / max(len1, len2)
        self.logger.debug("Similarity between '%s' and '%s' is %.3f", title1, title2, ratio)

        return ratio > self.similarityThreshold

    def cleanupTitles(self, titles = None):
        """Given a set of strings, it de-duplicates the ones
        which are similar enough.
        For instance "Star Wars: a new hope" and "Star Wars - A New Hope"
        should be deemed similar and reported only once.
        """
        assert isinstance(titles, frozenset)
        assert len(titles) > 0

        # remove newlines --  some titles arrive in more than one line
        titlesList = [x.replace("\n", " ") for x in titles]

        # set of movies discarded as similar to other ones, captured here for debugging purposes
        similar = frozenset([])

        for ptr in range(0, len(titlesList)):
            for cmp in range(ptr + 1, len(titlesList)):
                if self.isSimilar(titlesList[ptr], titlesList[cmp]):
                    similar = similar.union([titlesList[cmp]])
        self.logger.debug("Similar titles omitted:\n%s", similar)

        # omit the similar ones from the output
        cleanedTitles = titles.difference(similar)

        return cleanedTitles

###
#
# main entry point
#
###
if __name__ == "__main__":
    # Parse arguments from command line
    parser = argparse.ArgumentParser(description = 'Scraper is a python app to monitor the movie offering.')
    parser.add_argument('--dbfile', '-db',
                        required = True,
                        help = 'The sqlite db file to be used.')
    parser.add_argument('--logLevel', '-log',
                        required = False,
                        choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help = 'The level of output for logging. Defaults to INFO.')
    parser.add_argument('--location', '-loc',
                        required = True,
                        help = 'The location for which to collect data.')

    args = parser.parse_args()

    movieLogger.MovieLoggger().initLogger(level = args.logLevel)
    S = Scraper(dbfile = args.dbfile)

    allLocations = S._source.getAllLocations()
    S.logger.info("Locations definitions found for: %s", allLocations)

    S.logger.info("Looking for: %s...", args.location)
    t = S.getMoviesTitles(args.location)
    S.logger.info("%s - Got %d movies:", args.location.upper(), len(t))
    S.logger.info(pformat(t))

#    t = S.getMoviesTitles("Milano")
#    S.logger.info("MILANO - Got %d movies:", (len(t)))
#    S.logger.info(pformat(t))
