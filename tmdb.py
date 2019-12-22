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
        It walks through the first two pages of the possible responses, returning one dictionary with
        the first 40 matching records.
        If there are more results, the flag 'incomplete_result_set' is flagged to "true", and
        the number of all possible results is stored in 'total_results'. 
        """
        moviesFound = self.get(self._TIMDB_API_URL + \
                              "search/movie?language=%s&query=%s&page=1&include_adult=true" % \
                              (language, title))

        if moviesFound == None:
            self.logger.warn("No response got back when searching for \"%s\"" % (title))
            return {'results': [], 'incomplete_result_set': True}

        elif moviesFound != None and moviesFound['total_pages'] > 1:
            # skip if we need more than 2 pages (results are too many to match reliably)
            if moviesFound['total_pages'] > 2:
                self.logger.info("Too many results to query (%d pages for %d title matching \"%s\"): manual search needed." %
                                 (moviesFound['total_pages'], moviesFound['total_results'], title))
                moviesFound['incomplete_result_set'] = True

            else:
                # 2 pages total: get the second page and return the set
                moviesFound['incomplete_result_set'] = False

                newMoviesFound = self.get(self._TIMDB_API_URL + \
                                 "search/movie?language=%s&query=%s&include_adult=true&page=2" % \
                                 (language, title))
                if (isinstance(newMoviesFound, dict) and 'results' in moviesFound.keys()):
                    moviesFound['results'] += newMoviesFound['results']

        else:
            # 1 page of results is all there is: we're ok
            moviesFound['incomplete_result_set'] = False

        self.logger.debug("Search for '%s' returned %d results (out of %d)." % \
                      (title, len(moviesFound['results']), moviesFound['total_results']))
        return moviesFound

    def get(self, url = None):
        """
        Issue a GET request and returns the response deserialized from json as a dict,
        unless the return code is an error.

        It automatically append the user's key, so that all requests are through the
        same login.
        """
        response = None

        try:
            if (url.find('?') == -1):
                response = requests.get(url + "?" + self._KEY_ARG)
            else:
                response = requests.get(url + "&" + self._KEY_ARG)

        except BaseException as err:
            self.logger.error("Response was: %s\n%s" % (str(response), str(err)))
            return None

        if response != None and 'x-ratelimit-remaining' in response.headers._store.keys():
            reqLeft = int(response.headers._store['x-ratelimit-remaining'][1])
            self.logger.debug("Remaining requests for the next 10 seconds %d" % (reqLeft))
            if reqLeft <= 3:
                self.logger.debug("Remaining requests below limit: sleeping for 500ms")
                sleep(0.5)

        if response.status_code > 299:
            self.logger.error("Response was error: %d, %s" % (response.status_code, response))
            # TODO: add error handling bubbling it up to the caller
            # use: json.loads(('{"error": "True", "error message": "No title found."}')
            return None
        else:
            return json.loads(response.text)

    def storeConfigurations(self):
        """
        Gets the site's configuration for static references (URLs, keys, etc.)
        from TMD and stores it locally.
        """
        self._SITE_CONFIG = self.get(self._TIMDB_API_URL + "configuration")
