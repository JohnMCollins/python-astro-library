"""Database operations"""

# @Author: John M Collins <jmc>
# @Date:   2018-12-17T22:28:29+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dbops.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-17T10:19:16+00:00

# Get DB credentials from standard places

import os
import sys
import time
import pymysql
import dbcredentials

MAXTRIES = 10

class dbopsError(Exception):
    """Exception in case of error"""

class DBops_cursor:
    """Cursor class where we check for lock hold off"""

    def __init__(self, curs):
        self.cursor = curs
        self.connection = curs.connection
        self.lastrowid = 0

    def execute(self, *args):
        """Check execution of args"""
        tries = 1
        while tries <= MAXTRIES:
            try:
                ret =  self.cursor.execute(*args)
                self.lastrowid = self.cursor.lastrowid
                return  ret
            except pymysql.OperationalError:
                print("Backing off for {:d} seconds".format(tries), file=sys.stderr)
                time.sleep(tries)
            tries += 1
        raise dbopsError("Exceeded number of tries")

    def fetchall(self):
        """Duplicate fetchall"""
        return  self.cursor.fetchall()

    def fetchone(self):
        """Duplicate fetchone"""
        return  self.cursor.fetchone()

def opendb(name):
    """Open the database with the name given"""

    try:
        dbc = dbcredentials.DBcredfile()
        creds = dbc.get(name)
    except dbcredentials.DBcredError as e:
        raise dbopsError(e.args[0])

    if creds.login is None:
        try:
            return  pymysql.connect(host=creds.host, user=creds.user, passwd=creds.password, db=creds.database)
        except pymysql.OperationalError as e:
            raise dbopsError("Could  not connect to database error was " + e.args[1])

    # We need SSH tunnel, first see if we've got one already

    try:
        return  pymysql.connect(host='localhost', port=int(creds.localport), user=creds.user, passwd=creds.password, db=creds.database)
    except pymysql.OperationalError as e:
        if e.args[0] != 2003:
            raise dbopsError("Could  not connect to database error was " + e.args[1])

    if os.fork() == 0:
        os.execvp("ssh", ["ssh", "-nNT", "-L", "%d:localhost:%d" % (int(creds.localport), int(creds.remoteport)), "%s@%s" % (creds.login, creds.host)])
        sys.exit(255)

    time.sleep(5)
    try:
        return  pymysql.connect(host='localhost', port=int(creds.localport), user=creds.user, passwd=creds.password, db=creds.database)
    except pymysql.OperationalError as e:
        raise dbopsError("Could  not connect to database after SSH tunnel error was " + e.args[1])
