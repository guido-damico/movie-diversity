'''
Created on December 15, 2018

@author: Guido
'''
import sys
import unittest
import xmlrunner
import movieLogger
import logging

from utils.timdb import imdbRestClient

class testMovieDbClasses(unittest.TestCase):
    """
    Tests for the movieDbClasses class.
    """

    logger = None
    imdbClient = None

    _IMDB_API_KEY = "09ac37f03df193fc3b81b7f4c097e8e2"
    _FULL_TEST_URL = "https://api.themoviedb.org/3/movie/144?api_key=" + _IMDB_API_KEY + "&language=en-US"
    _MOVIE_ID = 144
    _MOVIE_TITLE = "Wings of Desire"
    _SEARCH_STRIING_1 = "Il cielo sopra Berlino"
    _SEARCH_STRIING_2 = "rosso"
    _SEARCH_STRIING_2_TITLE = "Deep Red"
    _SEARCH_STRIING_2_NUMBER = 129
    _SEARCH_STRIING_2_PAGES = 7
    _SEARCH_STRIING_2_ORIGINAL_TITLE = "Profondo rosso"

    @classmethod
    def setUpClass(cls):
        super(testMovieDbClasses, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('INFO')

    def setUp(self):
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)
        self.imdbClient = imdbRestClient()

        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testSimpleGet(self):
        self.logger.info("Requesting GET: %s" % self._FULL_TEST_URL)
        resp = self.imdbClient.get(url = self._FULL_TEST_URL)
        self.logger.debug("Got back: %s" % resp)

    def testGetTitleFromId(self):
        self.logger.info("Looking up movie by Id : %s" % self._MOVIE_ID)
        resp = self.imdbClient.getTitle(self._MOVIE_ID)
        assert resp['title'] == self._MOVIE_TITLE, \
            "Expected title for movie %d to be '%s', got: %s" % (self._MOVIE_ID, self._MOVIE_TITLE, resp['title'])

    def testSearchByTitle(self):
        self.logger.info("Searching movies by keyword : %s" % self._SEARCH_STRIING_1)
        resp = self.imdbClient.searchByTitle(self._SEARCH_STRIING_1)
        assert len(resp['results']) == 1, \
            "Expected 1 result, got %d" % len(resp['results'])
        assert resp['results'][0]['title'] == self._MOVIE_TITLE, \
            "Expected title '%s', got '%s'" % (self._MOVIE_TITLE, resp['results'][0]['title'])

        self.logger.info("Searching movies by keyword : %s" % self._SEARCH_STRIING_2)
        resp = self.imdbClient.searchByTitle(self._SEARCH_STRIING_2)
        assert len(resp['results']) == 20, \
            "Expected 20 results, got %d" % len(resp['results'])
        assert resp['total_results'] == self._SEARCH_STRIING_2_NUMBER, \
            "Expected %s total_results, got %d" % (self._SEARCH_STRIING_2_NUMBER, resp['total_results'])

        assert resp['total_pages'] == self._SEARCH_STRIING_2_PAGES, \
            "Expected %d pages of results, got %d" % (self._SEARCH_STRIING_2_PAGES, resp['total_pages'])
        assert resp['results'][0]['title'] == self._SEARCH_STRIING_2_TITLE, \
            "Expected title '%s', got '%s'" % (self._SEARCH_STRIING_2_TITLE, resp['results'][0]['title'])
        assert resp['results'][0]['original_title'] == self._SEARCH_STRIING_2_ORIGINAL_TITLE, \
            "Expected original title '%s', got '%s'" % (self._SEARCH_STRIING_2_ORIGINAL_TITLE, resp['results'][0]['original_title'])

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
        # suite = unittest.TestLoader().loadTestsFromTestCase(testMovieDbClasses)
        # unittest.TextTestRunner(verbosity = 3).run(suite)
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports-imdbrestclient'))
