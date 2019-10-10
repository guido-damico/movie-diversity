"""
Client to query the movie db (TIMDB: https://developers.themoviedb.org/3/getting-started).

Created on Dec 15, 2018

@author: guido
"""

import requests
import logging
from time import sleep
import movieLogger
import utils.stringUtils as stringUtils
import utils.propertiesFileReader as propertiesFileReader

import json

class restClientError(Exception):
    """
    Error class for the tmdb rest client. 
    """

    def __init__(self, message):
        self.message = message

class tmdbRestClient(object):
    """
    Rest client to interface with TMDB: https://developers.themoviedb.org/3/getting-started
    """
    logger = None

    _TIMDB_API_URL = "https://api.themoviedb.org/3/"
    _TMDB_PROPERTIES_FILE = 'tmdb.properties'
    _KEY_ARG = ""  # should be stored in the _TMDB_PROPERTIE_FILE file
    _LANG_ARG = "&language=en-US"
    _SITE_CONFIG = {}

    def __init__(self):
        """
        Constructor. Init the logger, read the tmdb key, and get the remote configurations.
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        # read the key to connect to the db from the properties file
        props = propertiesFileReader.PropertiesFileReader().readPropertiesFile(self._TMDB_PROPERTIES_FILE)
        self._KEY_ARG = "api_key=" + props['api_key']

        self.storeConfigurations()

    def get(self, url = None):
        """
        Issue a GET request and returns the response deserialized from json as a dict,
        unless the return code is an error.

        It automatically append the user's key, so that all requests are through the
        same login.
        """
        if (url.find('?') == -1):
            response = requests.get(url + "?" + self._KEY_ARG)
        else:
            response = requests.get(url + "&" + self._KEY_ARG)

        if response.status_code > 299:
            self.logger.error("Response was error: %d, %s" % (response.status_code, response))
            # TODO: add error handling bubbling it up to the caller
            # use: json.loads(('{"error": "True", "error message": "No title found."}')

        return json.loads(response.text)

    def storeConfigurations(self):
        """
        Gets the site's configuration for static references (URLs, keys, etc.)
        from TMD and stores it locally.
        """
        self._SITE_CONFIG = self.get(self._TIMDB_API_URL + "configuration")

    def getTitleById(self, movieId = None):
        """
        Gets the record of the movie with that id.
        """

        # Check that we have a valid integer
        if not stringUtils.isAnInt(movieId):
            raise restClientError("Invalid Id, need an integer, got %s" % movieId)

        return self.get(self._TIMDB_API_URL + "movie/%s" % (str(movieId)))

    def searchByTitle(self, title = None, language = "en"):
        """
        Search the db for a movie by that title in that language, defaults the "en" for English.
        It walks through all the pages of the possible responses, returning one dictionary with all
        the matching records.
        """
        moviesFound = self.get(self._TIMDB_API_URL + \
                              "search/movie?language=%s&query=%s&page=1&include_adult=true" % \
                              (language, title))

        if moviesFound['total_pages'] > 1:
            for newPage in range(2, moviesFound['total_pages'] + 1):
                newMoviesFound = self.get(self._TIMDB_API_URL + \
                                 "search/movie?language=%s&query=%s&include_adult=true&page=%d" % \
                                 (language, title, newPage))
                moviesFound['results'] += newMoviesFound['results']
                moviesFound['page'] = newMoviesFound['page']
                # To avoid hitting TMDB requests limits, space requests 500 msec apart
                sleep(0.500)

        self.logger.debug("Querying for '%s' returned %d results (expected %d)." % \
                          (title, len(moviesFound['results']), moviesFound['total_results']))

        return moviesFound

