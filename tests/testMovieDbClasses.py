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

    # _dbName = '/home/guido/work/git/movie-diversity/movieDiversity.db'
    _dbName = '/home/guido/work/git/movie-diversity/workingDb.db'
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
        movieLogger.MovieLoggger().initLogger('DEBUG')

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
        # for cleaning, no need to stay at DEBUG level
        movieLogger.MovieLoggger().resetLoggingLevel('INFO')
        self.util.cleanUpTestData()
        movieLogger.MovieLoggger().resetLoggingLevel('DEBUG')
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

    def testInsertSites(self):
        """
        Verifies the 1-to-many relationship between Locations and sites works.
        """
        self.logger.info("Testing creation of Locations and Sites")

        self.logger.debug("\tCreating locations.")
        loc1 = Locations(name = self.util.getNewTestName() + "Poggibonsi", language = "toscano")
        loc2 = Locations(name = self.util.getNewTestName() + "Corleone", language = "siculo")

        self.logger.debug("\tCreating sites.")
        aSite1 = movieDbClasses.Sites(name = self.util.getNewTestName() + "sitePoggi",
                                     url = "example.com",
                                     title_xpath = "*",
                                     active = 1)

        aSite2 = movieDbClasses.Sites(name = self.util.getNewTestName() + "sitePoggi_2",
                                     url = "example.it",
                                     title_xpath = "!*",
                                     active = 1)
        self.logger.debug("\tAdding sites to loc 1.")
        loc1.sites.append(aSite1)
        loc1.sites.append(aSite2)

        self.session.add(loc1)
        self.session.add(loc2)
        self.session.commit()

        self.session.add(aSite1)
        self.session.add(aSite2)
        self.session.commit()

        self.assertTrue(loc1.id != None, "Loc1 should have been committed correctly and have a valid id.")
        self.assertTrue(loc2.id != None, "Loc2 should have been committed correctly and have a valid id.")

        self.assertTrue(aSite1.id != None, "aSite1 should have been committed correctly and have a valid id.")
        self.assertTrue(aSite2.id != None, "aSite2 should have been committed correctly and have a valid id.")

    def testInsertTitlesInLocations(self):
        """
        Verifies the 1-to-many relationship between Locations and sites works.
        """
        self.logger.info("Testing creation of Locations and Titles(InLocation)")

        self.logger.debug("\tCreating locations.")
        loc1 = Locations(name = self.util.getNewTestName() + "Poggibonsi", language = "toscano")
        loc2 = Locations(name = self.util.getNewTestName() + "Corleone", language = "siculo")
        self.session.add(loc1)
        self.session.add(loc2)
        self.session.commit()

        self.assertTrue(loc1.id != None, "Loc1 should have been committed correctly and have a valid id.")
        self.assertTrue(loc2.id != None, "Loc2 should have been committed correctly and have a valid id.")

        self.logger.debug("\tCreating titles.")
        aTitle1 = Titles(title = self.util.getNewTestName())
        aTitle2 = Titles(title = self.util.getNewTestName())
        self.session.add(aTitle1)
        self.session.add(aTitle2)
        self.session.commit()

        self.assertTrue(aTitle1.id != None, "aTitle1 should have been committed correctly and have a valid id.")
        self.assertTrue(aTitle2.id != None, "aTitle2 should have been committed correctly and have a valid id.")

        self.logger.debug("\tLinking all titles to all locations.")
        aTitle1InLoc1 = TitlesInLocations(titles_ref = aTitle1.id, locations_ref = loc1.id)
        aTitle2InLoc1 = TitlesInLocations(titles_ref = aTitle2.id, locations_ref = loc1.id)
        aTitle1InLoc2 = TitlesInLocations(titles_ref = aTitle1.id, locations_ref = loc2.id)
        aTitle2InLoc2 = TitlesInLocations(titles_ref = aTitle2.id, locations_ref = loc2.id)
        self.session.add(aTitle1InLoc1)
        self.session.add(aTitle2InLoc1)
        self.session.add(aTitle1InLoc2)
        self.session.add(aTitle2InLoc2)
        self.session.commit()

        self.assertTrue(aTitle1InLoc1.id != None, "aTitle1InLoc1 should have been committed correctly and have a valid id.")
        self.assertTrue(aTitle2InLoc1.id != None, "aTitle2InLoc1 should have been committed correctly and have a valid id.")
        self.assertTrue(aTitle1InLoc2.id != None, "aTitle1InLoc2 should have been committed correctly and have a valid id.")
        self.assertTrue(aTitle2InLoc2.id != None, "aTitle2InLoc2 should have been committed correctly and have a valid id.")

        self.logger.info("Insertion completed.")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSource']
    if len(sys.argv) < 2 or sys.argv[1] != "exportXML":
        unittest.main()
    else:
        del sys.argv[1]  # remove the exportXML flag, which is not to be passed to the runner
        unittest.main(testRunner = xmlrunner.XMLTestRunner(output = 'test-reports-moviedbclasses'))
