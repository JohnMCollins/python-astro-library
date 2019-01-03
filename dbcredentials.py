# @Author: John M Collins <jmc>
# @Date:   2018-11-24T20:45:40+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dbcredentials.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-20T23:02:07+00:00


# Get DB credentials from standard places

import configparser
import os.path
import os

configfilepaths = ("/etc/dbcred.ini", os.path.expanduser("~/lib/dbcred.ini"), os.path.abspath('.dbcred.ini'))
selectconfig = dict(current = 2, lib = 1, system = 0)

try:
    defaultuser = os.environ['LOGNAME']
except KeyError:
    defaultuser = None

class DBcredError(Exception):
    pass

class DBcred(object):
    """This class uses configparser to read and optionally write a "ini" type file
    of database credentials.
    This can be ".dbcred.ini" in the current directory,
    ~/lib/dbcred.ini in "lib" of the user's home directory or
    /etc/dbcredi.ini
    We work in terms of tuples (host, dbname, user, password)"""

    def __init__(self):
        global configfilepaths
        self.cparser = configparser.ConfigParser()
        self.cparser.read(configfilepaths)

    def get(self, name):
        """Get credentials for the name"""
        try:
            sect = self.cparser[name]
        except KeyError:
            raise DBcredError("Section " + name + " not known")
        try:
            return  (sect.get('host', 'localhost'), sect['database'], sect.get('user', defaultuser), sect['password'])
        except KeyError as e:
            raise DBcredError("Section " + name + " not fully defined missing " + e.args[0])

    def set_defaults(self, creds):
        """Set defaults according to list.
        Items in list are new value or False to leave unchanged NOne to remove"""

        for optn, val in zip(('host', 'database', 'user', 'password'), creds):
            if  val is None:
                self.cparser.remove_option('DEFAULT', optn)
            elif val:
                self.cparser.set('DEFAULT', optn, val)

    def set_creds(self, name, creds):
        """Set crdds for named according to list.
        Items in list are new value or False to leave unchanged NOne to remove"""

        if not self.cparser.has_section(name):
            self.cparser.add_section(name)

        for optn, val in zip(('host', 'database', 'user', 'password'), creds):
            if  val is None:
                self.cparser.remove_option(name, optn)
            elif val:
                self.cparser.set(name, optn, val)

    def delcreds(self, name):
        """Delete credentials for given DB"""
        self.cparser.remove_section(name)


    def write(self, filename = "lib"):
        """Write credentials to filename.
        Special cases of filename are "current", "lib" and "sys" to
        write to standard names in current directory, ~/lib and system
        respectively"""

        global configfilepaths, selectconfig

        if filename in selectconfig:
            filename = configfilepaths[selectconfig[filename]]
        try:
            outf = open(filename, "wb")
        except IOError as e:
            raise DBcredError("Cannoto open file " + filename + " - " + e.args[1])

        self.cparser.write(outf)
        outf.close()
