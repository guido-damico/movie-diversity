"""
Created on May 5, 2017

@author: Guido

Main module to perform the MovieDiversity data collection app.
"""
import logging
import argparse
from pprint import pformat
import requests
from lxml import html
import sources
import movieLogger
from utils import stringUtils

class Scraper(object):
    """
        Scraper implementation class.

        Implements the Movie data collection functions and depends on
        the Sources and movieLogger.MovieLogger classes.
    """
    _source = None
    logger = None

    def __init__(self, dbfile = None):
        """
        Builds a local instance of the Sources class and
        one of the MovieLogger engine.
        """
        self._source = sources.Sources(dbfile = dbfile)
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        self.logger.info("Scraper instance inited.")

    def updateLocationMovies(self, locationName = None):
        """
        Given a location name, fetches the data off the net and
        populates the db.
        """

        # Gets the movie titles
        locationData = self._source.getLocationData(locationName = locationName)
        assert isinstance(locationData, type([])), \
                          "Expected a list for locations, instead got %s" % type(locationData)
        titles = self.getMoviesTitlesInLocation(locationName = locationName)

        successfullyInserted = 0
        # stores each title
        for title in titles:
            titleId = self._source.insertTitleInLocation(title, locationData[0]['locations_ref'])[0]
            if titleId is None:
                self.logger.error("Could not identify '%s' correctly, skipping it.", title)
            else:
                self._source.insertShow(titleId, locationData[0]['locations_ref'])
                successfullyInserted += 1
                self.logger.debug("Inserted show %d for '%s' in %s (%d) today.",
                                  successfullyInserted,
                                  title,
                                  locationName,
                                  locationData[0]['locations_ref'])

        # logs some information
        self.logger.info("Inserted %d new shows for today in %s.",
                         len(titles),
                         locationName)
        if successfullyInserted != len(titles):
            self.logger.warning("Skipped %d shows for %s",
                                len(titles) - successfullyInserted,
                                locationName)

    def getMoviesTitlesInLocation(self, locationName = None):
        """
        Given the id of a location, it returns a
        set of all movie titles playing there today.
        """
        self.logger.info("Looking for movie titles in %s.", locationName)

        titles = set()

        data = self._source.getLocationData(locationName)

        # for every active site in the list, get the titles and insert them in the output set
        for site in data:
            if site['active']:
                titles = titles.union(self.getMoviesTitlesFromURL(url = site['url'],
                                                                  title_xpath = site['title_xpath']))
                self.logger.debug("Got titles from site %s, now I have %d in total.",
                                  site['name'],
                                  len(titles))

        # clean up before sending back
        return self.cleanupTitles(titles)

    def getMoviesTitlesFromURL(self, url = "", title_xpath = ""):
        """
        Function which given a URL and an xpath query to identify the titles of the movies on the
        page returned by the URL, it returns a set of all the titles.
        """
        self.logger.info("Querying %s ...", url)

        page = requests.get(url)
        self.logger.debug("Returned status: %s. Got %d bytes back.",
                          page.status_code,
                          len(page.content))

        tree = html.fromstring(page.content)
        titles = set(tree.xpath(title_xpath))
        self.logger.info("Identified %d titles.", len(titles))

        return titles

    def cleanupTitles(self, titles = None):
        """
        Given a set of strings, it de-duplicates the ones
        which are similar enough.

        For instance "Star Wars: a new hope" and "Star Wars - A New Hope"
        should be deemed similar and reported only once.
        """
        assert isinstance(titles, set), "Expecting a set of titles, got %s" % type(titles)
        if len(titles) == 0:
            return set()

        # remove newlines --  some titles arrive in more than one line
        titlesList = [x.replace("\n", " ") for x in titles]

        # set of movies discarded as similar to other ones, captured here for debugging purposes
        similar = set()

        # check if the title is a duplicate of a similar one, if so skip it
        for first in range(0, len(titlesList)):
            for second in range(first + 1, len(titlesList)):
                if stringUtils.isSimilar(titlesList[first], titlesList[second]):
                    self.logger.debug("Found title '%s', similar to '%s', using the latter.",
                                      titlesList[first],
                                      titlesList[second])
                    similar.add(titlesList[first])

                    break

        self.logger.debug("Similar titles omitted:\n%s", pformat(similar))

        # omit the similar ones from the output
        cleanedTitles = titles.difference(similar)

        return cleanedTitles

# ##
#
# main entry point
#
# ##
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

    # Init the logging system
    movieLogger.MovieLoggger().initLogger(level = args.logLevel)

    S = Scraper(dbfile = args.dbfile)

    allLocations = S._source.getAllLocations()
    S.logger.info("Locations definitions found for: %s", allLocations)

    S.logger.info("Looking for: %s...", args.location)
    S.updateLocationMovies(args.location)
    S.logger.info("End run.")

