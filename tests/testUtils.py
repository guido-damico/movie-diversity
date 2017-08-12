'''
Created on May 21, 2017

@author: Guido
'''
from contextlib import closing
import dbUtils as db

class Utils(object):
    """
    Utilities to maintain the tests cleanly.
    """
    _conn = None
    _logger = None
    _baseTestInt = 0
    baseTestName = "__TEST__"

    def __init__(self, dbfile = None, logger = None):
        self._logger = logger
        self._conn = db.connect(dbfile = dbfile)

    def getNewTestName(self):
        """
        Generates a string different every time (for this instance and this run, of course)
        to be used as test titles.
        """
        self._baseTestInt += 1
        return self.baseTestName + str(self._baseTestInt)

    def getDbTestRecords(self):
        """
        Returns a dictionary listing all the testing records found in the db.
        These records can be safely deleted.
        """
        output = {'titles': 0,
                  'titles_in_locations': 0,
                  'shows': 0}

        with (closing(self._conn.cursor())) as cur:
            cur.execute("SELECT id FROM titles WHERE title like ?;", (self.baseTestName + "%",))
            recs = cur.fetchall()
            output['titles'] = [x['id'] for x in recs]

            placeholdersTId = ', '.join('?' * len(output['titles']))

            qry = "SELECT id FROM titles_in_locations WHERE titles_ref in (%s);" % placeholdersTId
            cur.execute(qry, output['titles'])
            recs = cur.fetchall()
            output['titles_in_locations'] = [x['id'] for x in recs]
            placeholdersTILId = ', '.join('?' * len(output['titles_in_locations']))

            qry = "SELECT id FROM shows WHERE titles_in_locations_ref in (%s);" % placeholdersTILId
            cur.execute(qry, output['titles_in_locations'])
            recs = cur.fetchall()
            output['shows'] = [x['id'] for x in recs]

        return output

    def checkDbDataTestNames(self):
        """
        Raises an exception if it finds that the db is not clean.
        To clean it up call cleanUpTestData().
        Ro see which record are triggering the exception run getDbTestRecords().
        """
        alreadyThere = self.getDbTestRecords()
        if len(alreadyThere['titles']) + len(alreadyThere['shows']) > 0:
            raise RuntimeError("Name conflict: found already %d records.\n" %\
                               (len(alreadyThere['titles']) + len(alreadyThere['shows'])) + \
                               "Please clean up the testing db first.")

    def cleanUpTestData(self):
        """
        Gets in to the db and erases all testing data.
        """
        with (closing(self._conn.cursor())) as cur:
            testRecords = self.getDbTestRecords()
            totLen = len(testRecords['titles']) + len(testRecords['titles_in_locations']) + len(testRecords['shows'])

            self._logger.info("Cleaning up: Found %d titles test record(s).", len(testRecords['titles']))
            self._logger.info("Cleaning up: Found %d titles_in_locations test record(s).", len(testRecords['titles_in_locations']))
            self._logger.info("Cleaning up: Found %d shows test record(s).", len(testRecords['shows']))

            if totLen > 0:
                try:
                    self._logger.info("Cleaning up %d test record(s).", totLen)

                    placeholdersTId = ', '.join('?' * len(testRecords['titles']))
                    placeholdersTILId = ', '.join('?' * len(testRecords['titles_in_locations']))

                    qry = "DELETE FROM shows WHERE titles_in_locations_ref in (%s);" % placeholdersTILId
                    cur.execute(qry, testRecords['titles_in_locations'])
                    self._logger.info("Deleted %d shows test record(s).", cur.rowcount)

                    qry = "DELETE FROM titles_in_locations WHERE id in (%s);" % placeholdersTILId
                    cur.execute(qry, testRecords['titles_in_locations'])
                    self._logger.info("Deleted %d titles_in_locations test record(s).", cur.rowcount)

                    qry = "DELETE FROM titles WHERE id in (%s);" % placeholdersTId
                    cur.execute(qry, testRecords['titles'])
                    self._logger.info("Deleted %d titles test record(s).", cur.rowcount)

                except Exception as e:
                    self._logger.error("Failed to properly clean up the test data! You may need to clean up manually to resume operations.")
                    raise AssertionError(e)
