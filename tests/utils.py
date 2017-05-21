'''
Created on May 21, 2017

@author: Guido
'''
import sqlite3
from contextlib import closing

class Utils(object):

    _conn = None
    _logger = None
    _baseTestInt = 0
    baseTestName = "__TEST__"

    def __init__(self, dbfile = None, logger = None):
        self._logger = logger
        self._conn = sqlite3.connect(dbfile, isolation_level = None)
        self._conn.row_factory = sqlite3.Row
    
    def getNewTestName(self):
        self._baseTestInt += 1
        return self.baseTestName + str(self._baseTestInt)

    def getDbTestRecords(self):
        output = {'titles': 0,
                  'shows': 0}

        with (closing(self._conn.cursor())) as cur:
            cur.execute("SELECT id FROM titles WHERE title like ?;", (self.baseTestName + "%",))
            recs = cur.fetchall()
            output['titles'] = [x['id'] for x in recs]

            placeholders = ', '.join('?' * len(output['titles']))
            qry = "SELECT id FROM shows WHERE titles_ref in (%s);" % placeholders
            cur.execute(qry, output['titles'])
            recs = cur.fetchall()
            output['shows'] = [x['id'] for x in recs]

        return output
            
    def checkDbDataTestNames(self):
        alreadyThere = self.getDbTestRecords()
        if len(alreadyThere['titles']) + len(alreadyThere['shows']) > 0:
            raise RuntimeError("Name conflict: found already %d records.\n" %\
                               (len(alreadyThere['titles']) + len(alreadyThere['shows'])) + \
                               "Please clean up the testing db first.")
    
    def cleanUpTestData(self):
        with (closing(self._conn.cursor())) as cur:
            testRecords = self.getDbTestRecords()
            totLen = len(testRecords['titles']) + len(testRecords['shows'])

            self._logger.info("Found %d test record(s).", totLen)

            if totLen > 0:
                self._logger.info("Cleaning up %d test record(s).", totLen)

                placeholders = ', '.join('?' * len(testRecords['titles']))

                qry = "DELETE FROM shows WHERE titles_ref in (%s);" % placeholders
                cur.execute(qry, testRecords['titles'])

                qry = "DELETE FROM titles WHERE id in (%s);" % placeholders
                cur.execute(qry, testRecords['titles'])
