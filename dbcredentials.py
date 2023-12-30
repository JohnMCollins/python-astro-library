"""Get DB credentials from standard places"""

import configparser
import os.path
import os
import io
from cryptography.fernet import Fernet, InvalidToken

configfilepaths = ("/etc/dbcred.ini", os.path.expanduser("~/lib/dbcred.ini"), os.path.abspath('.dbcred.ini'))
selectconfig = {"current" : 2, "lib" : 1, "system" : 0}
fern_key = None
try:
    with open(os.path.expanduser("~/.jmc/sec.key"), "rb") as fkin:
        keyf = fkin.read()
    fern_key = Fernet(keyf)
except (IOError, ValueError):
    pass

try:
    defaultuser = os.environ['LOGNAME']
except KeyError:
    defaultuser = None

class DBcredError(Exception):
    """For moans about credential errors"""

class DBcred:
    """Representation of credentials as class"""

    def __init__(self, host = None, database = None, user = None, password = None, login = None, localport = None, remoteport = None):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.login = login
        self.localport = localport
        self.remoteport = remoteport

    def incomplete(self):
        """Return if incompletely defined"""
        if self.host is None or self.database is None or self.user is None or self.password is None:
            return  True
        if self.login is not None and self.localport is None:
            return  True
        return  False

class DBcredfile:
    """This class uses configparser to read and optionally write a "ini" type file
    of database credentials.
    This can be ".dbcred.ini" in the current directory,
    ~/lib/dbcred.ini in "lib" of the user's home directory or
    /etc/dbcredi.ini
    We work in terms of tuples (host, dbname, user, password)"""

    def __init__(self):
        self.cparser = configparser.ConfigParser()
        for cpth in configfilepaths:
            try:
                with open(cpth, 'rb') as cfil:
                    contents = cfil.read()
            except IOError:
                continue
            try:
                self.cparser.read_string(contents.decode())
                continue
            except configparser.Error:
                pass
            try:
                contents = fern_key.decrypt(contents)
            except InvalidToken:
                continue
            try:
                self.cparser.read_string(contents.decode())
            except configparser.Error:
                pass

    def get(self, name):
        """Get credentials for the name"""
        try:
            sect = self.cparser[name]
        except KeyError:
            raise DBcredError("Section " + name + " not known")
        ret = DBcred(host = sect.get('host', 'localhost'),
                    database = sect.get('database'),
                    user = sect.get('user', defaultuser),
                    password = sect.get('password'),
                    login = sect.get('login'),
                    localport = sect.get('localport'),
                    remoteport = sect.get('remoteport'))
        if ret.incomplete():
            raise DBcredError("Section " + name + " not fully defined")
        return  ret

    def set_value(self, sect, optn, val):
        """Routine to impletment setting value in section, if value is False leave unchanged if None delete"""

        if val is None:
            self.cparser.remove_option(sect, optn)
        elif val:
            self.cparser.set(sect, optn, val)

    def set_values(self, sect, creds):
        """Set values according to credentials"""
        self.set_value(sect, "host", creds.host)
        self.set_value(sect, "database", creds.database)
        self.set_value(sect, "user", creds.user)
        self.set_value(sect, "password", creds.password)
        self.set_value(sect, "login", creds.login)
        self.set_value(sect, "localport", creds.localport)
        self.set_value(sect, "remoteport", creds.remoteport)

    def set_defaults(self, creds):
        """Set defaults according to arg
        Items in arg are new value or False to leave unchanged NOne to remove"""

        self.set_values("DEFAULT", creds)

    def set_creds(self, name, creds):
        """Set crdds for named according to list.
        Items in list are new value or False to leave unchanged NOne to remove"""

        if not self.cparser.has_section(name):
            self.cparser.add_section(name)

        self.set_values(name, creds)

    def delcreds(self, name):
        """Delete credentials for given DB"""
        self.cparser.remove_section(name)

    def write(self, filename = "lib"):
        """Write credentials to filename.
        Special cases of filename are "current", "lib" and "sys" to
        write to standard names in current directory, ~/lib and system
        respectively"""

        outbuf = io.StringIO()
        self.cparser.write(outbuf)
        cont = outbuf.getvalue().encode()
        if fern_key is not None and filename != 'system':
            cont = fern_key.encrypt(cont)

        if filename in selectconfig:
            filename = configfilepaths[selectconfig[filename]]
        try:
            with open(filename, "wb") as outf:
                outf.write(cont)
        except IOError as e:
            raise DBcredError("Cannot write file " + filename + " - " + e.args[1])
