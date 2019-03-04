'''
Created on December 2, 2018

@author: Guido
'''
import sys
import inspect
import unittest
import xmlrunner
import movieLogger
import logging
import tests.utils

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import movieDbClasses
from movieDbClasses import Locations
from movieDbClasses import Sites
from movieDbClasses import Titles
from movieDbClasses import TitlesInLocations
from movieDbClasses import Shows
from movieDbClasses import Translations

class testMovieDbClasses(unittest.TestCase):
    """
    Tests for the movieDbClasses class.
    """

    logger = None
    session = None
    util = None

    _dbName = '/home/guido/work/git/movie-diversity/movieDiversity.db'
    _dbConnectString = 'sqlite:///' + _dbName

    _expectedClasses = [
            # movieDbBaseClass,
            Locations,
            Sites,
            Titles,
            TitlesInLocations,
            Shows,
            Translations
        ]

    _expectedColumns = {
            "Locations": [
                "id",
                "name",
                "language",
                ],
            "Sites" : [
                "id",
                "name",
                "url",
                "title_xpath",
                "active",
                "locations_ref",
                ],
            "Titles": [
                "id",
                "title",
                ],
            "TitlesInLocations": [
                "id",
                "titles_ref",
                "locations_ref",
                ],
            "Shows": [
                "id",
                "date",
                "titles_in_locations_ref",
               ],
            "Translations": [
                "id",
                "lang_from",
                "lang_to",
                "title_from_ref",
                "title_to_ref",
                ]
        }

    @classmethod
    def setUpClass(cls):
        super(testMovieDbClasses, cls).setUpClass()
        movieLogger.MovieLoggger().initLogger('INFO')

    def setUp(self):
        self.logger = logging.getLogger(movieLogger.MovieLoggger.LOGGER_NAME)

        unittest.TestCase.setUp(self)

        dbEngine = create_engine(self._dbConnectString)
        movieDbClasses.Base.metadata.bind = dbEngine
        DBSession = sessionmaker()
        DBSession.bind = dbEngine
        self.session = DBSession()

        self.util = tests.utils.Utils(dbfile = self._dbName,
                                      logger = self.logger)

        self.util.checkDbDataTestNames()

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testDbClasses(self):
        """
        Verifies that the package defines the expected classes (one per table).
        """
        missingClasses = []

        self.logger.info("*** Checking the classes in the package...")

        # Inspect (Python version of reflection) all classes defined in the module movieDbClasses
        allClasses = inspect.getmembers(movieDbClasses, inspect.isclass)

        # isolate only the ones for the table objects
        foundClazzez = [x for x in allClasses if repr(x[1])[8:].startswith("movieDbClasses") and not repr(x[1])[8:].endswith("movieDbBaseClass'>")]
        for clazz in foundClazzez:
            try:
                self._expectedClasses.index(clazz[1])
                self.logger.info("\tFound class: %s" % clazz[0])
            except ValueError:
                self.logger.error("Could not find class %s in the package!" % (clazz[0]))
                missingClasses.append(clazz[0])

        if len(missingClasses) > 0:
            self.logger.error("Missing classes: %s" % missingClasses)
        self.assertTrue(len(missingClasses) == 0, "Found one or more classes missing.")

        self.logger.info("Package check passed.")

    def testDbClassesColumns(self):
        """
        Verifies that the definitions of the db classes conform to the expectations.
        """
        self.logger.info("*** Verifying db classes definitions...")

        missingColumns = {}
        extraColumns = {}

        # Check all the classes in the module
        allClasses = inspect.getmembers(movieDbClasses, inspect.isclass)

        for clazz in [x[0] for x in allClasses if repr(x[1])[8:].startswith("movieDbClasses") and not repr(x[1])[8:].endswith("movieDbBaseClass'>")]:
            self.logger.info("Testing class %s", clazz)

            # 1. create one instance of that class
            cls = getattr(movieDbClasses, clazz)
            self.logger.info("\tCreated instance")

            # 2. query the db for the first item in that table
            rec = self.session.query(cls).first()
            self.logger.info("\tQueried db")

            # 3. isolate the name of this class
            typeRec = type(rec)
            recName = repr(typeRec)[23:repr(typeRec).rindex("'")]
            self.logger.info("\tFound class by name: %s", recName)

            # 4. get the list of its columns
            allRecColumns = [x.name for x in rec.__table__.columns]
            self.logger.info("\tGot all the columns")

            # 5. compare that list with the gold record
            expectedCols = self._expectedColumns[recName]
            missingColumns[recName] = [x for x in expectedCols if x not in allRecColumns]
            extraColumns[recName] = [x for x in allRecColumns if x not in expectedCols]
            self.logger.info("\tCompared all columns")

        # Final check to see if any column mismatch was found
        if (sum([ len(missingColumns[x]) for x in missingColumns ]) > 0 or \
            sum([ len(extraColumns[x]) for x in extraColumns ]) > 0):

            self.logger.error("Missing columns: %s" % missingColumns)
            self.logger.error("Extra columns: %s" % extraColumns)
            self.fail("Found column mismatch")
        else:
            self.logger.info("Columns check passed.")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports-moviedbclasses'))
