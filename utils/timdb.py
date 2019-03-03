"""
Client to query the movie db (TIMDB: https://developers.themoviedb.org/3/getting-started).

Created on Dec 15, 2018

@author: guido
"""

import requests
import logging
import movieLogger
import utils.stringUtils as stringUtils

import json

class restClientError(Exception):
    """
    Error class for the imdb rest client. 
    """

    def __init__(self, message):
        self.message = message

class imdbRestClient(object):
    """
    Rest client to interface with TIMDB: https://developers.themoviedb.org/3/getting-started
    """
    logger = None

    _IMDB_API_URL = "https://api.themoviedb.org/3/"
    _API_KEY_ARG = "api_key=09ac37f03df193fc3b81b7f4c097e8e2"

    def __init__(self, params = None):
        """
        Constructor
        """
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

    def get(self, url = None):
        """
        Issue a GET request and returns the response deserialized from json as a dict,
        unless the return code is an error.
        """
        response = requests.get(url)

        if response.status_code > 299:
            self.logger.warning("Response was error: %d, %s" % (response.status_code, response))

        return json.loads(response.text)

    def getTitle(self, id = None):
        """
        Gets the record of the movie with that id.
        """

        # Check that we have a valid integer
        if not stringUtils.isAnInt(id):
            raise restClientError("Invalid Id, need an integer, got %s" % id)

        return self.get(self._IMDB_API_URL + "movie/%s?%s" % (str(id), self._API_KEY_ARG))

    def searchByTitle(self, title = None):
        """
        Search the db for a movie by that title, works for any language,
        results are sent back for the English version.
        """
        moviesFound = self.get(self._IMDB_API_URL + "search/movie?%s&query=%s&page=1&include_adult=true" % (self._API_KEY_ARG, title))

        self.logger.debug("Querying for '%s' returned %d results." % (title, len(moviesFound)))

        return moviesFound

