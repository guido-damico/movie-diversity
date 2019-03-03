'''
Created on Jun 7, 2017

@author: Guido

Utilities to uniform the SQLite db handling.
'''

import sqlite3

def connect(dbfile = None):
    """
    Returns a connection to the specified sqlite db.
    """

    assert dbfile != None, "Cannot build a connection to a NULL file, please specify a valid name."

    out = sqlite3.connect(dbfile, isolation_level = None)
    # we use the Row class as factory so we have the columns' names as well
    out.row_factory = sqlite3.Row

    return out

def cursor(connection = None):
    """
    Returns a valid open cursor.
    """

    assert connection != None, "Cannot build a cursor on a NULL connection."

    out = connection.cursor()

    # we always want the foreign keys constraints enforced!
    out.execute("PRAGMA foreign_keys=ON;")

    return out
