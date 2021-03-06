'''
Created on December 15, 2018

@author: Guido
'''
import sys
import unittest
import xmlrunner
import movieLogger
import logging

from tmdb import tmdbRestClient

class testTimdb(unittest.TestCase):
    """
    Tests for the Timdb client.
    """

    logger = None
    tmdbRestClient = None

    _MOVIE_ID = 144
    _MOVIE_TITLE = "Wings of Desire"
    _MOVIE_TITLE_ORIG = "Der Himmel über Berlin"
    _SEARCH_STRIING_1 = "Il cielo sopra Berlino"
    _SEARCH_STRIING_2 = "rosso"
    _SEARCH_STRIING_2_TITLE = "Deep Red"
    _SEARCH_STRIING_2_NUMBER = 129
    _SEARCH_STRIING_2_PAGES = 7
    _SEARCH_STRIING_2_ORIGINAL_TITLE = "Profondo rosso"

    @classmethod
    def setUpClass(cls):
        super(testTimdb, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('INFO')

    def setUp(self):
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)
        self.tmdbRestClient = tmdbRestClient()

        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testGetTitleFromId(self):
        """Tests getting a movie from a known given ID."""
        self.logger.info("Looking up movie by Id : %s" % self._MOVIE_ID)
        resp = self.tmdbRestClient.getTitleById(self._MOVIE_ID)
        assert resp['title'] == self._MOVIE_TITLE, \
            "Expected title for movie %d to be '%s', got: %s" % (self._MOVIE_ID, self._MOVIE_TITLE, resp['title'])

    def testSearchByTitle(self):
        """Tests searching a movie by a generic title in different ways."""
        self.logger.info("Searching movies by keyword : %s" % self._SEARCH_STRIING_1)
        resp = self.tmdbRestClient.searchByTitle(title = self._SEARCH_STRIING_1, language = "it")
        assert len(resp['results']) == 1, \
            "Expected 1 result, got %d" % len(resp['results'])
        assert resp['results'][0]['original_title'] == self._MOVIE_TITLE_ORIG, \
            "Expected original title '%s', got '%s'" % (self._MOVIE_TITLE_ORIG, resp['results'][0]['title'])
        assert resp['results'][0]['title'] == self._SEARCH_STRIING_1, \
            "Expected Italian title '%s', got '%s'" % (self._SEARCH_STRIING_1, resp['results'][0]['title'])

        self.logger.info("Searching movies by keyword : %s" % self._SEARCH_STRIING_2)
        resp = self.tmdbRestClient.searchByTitle(self._SEARCH_STRIING_2)
        assert len(resp['results']) == resp['total_results'], \
            "Expected %d results, got %d" % (resp['total_results'], len(resp['results']))
        assert resp['total_results'] >= self._SEARCH_STRIING_2_NUMBER, \
            "Expected at least %s total_results, got %d" % (self._SEARCH_STRIING_2_NUMBER, resp['total_results'])

        assert resp['total_pages'] == self._SEARCH_STRIING_2_PAGES, \
            "Expected %d pages of results, got %d" % (self._SEARCH_STRIING_2_PAGES, resp['total_pages'])

        allResultsSet = set(x['title'] for x in resp['results'])
        assert self._SEARCH_STRIING_2_TITLE in allResultsSet, \
            "Expected title '%s' among the results, got '%s'" % (self._SEARCH_STRIING_2_TITLE, allResultsSet)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
        # suite = unittest.TestLoader().loadTestsFromTestCase(testMovieDbClasses)
        # unittest.TextTestRunner(verbosity = 3).run(suite)
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports-imdbrestclient'))
