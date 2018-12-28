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

    _FULL_TEST_URL = "https://api.themoviedb.org/3/movie/144?api_key=09ac37f03df193fc3b81b7f4c097e8e2&language=en-US"
    _MOVIE_ID = 144
    _MOVIE_TITLE = "Wings of Desire"

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

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports-imdbrestclient'))
