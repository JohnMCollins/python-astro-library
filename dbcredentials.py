# Get DB credentials from standard places

import ConfigParser
import os.path
import os

configfilepaths = ("/etc/dbcred.ini", os.path.expanduser("~/lib/dbcred.ini"), os.path.abspath('.dbcred.ini'))
selectconfig = dict(current = 2, lib = 1, system = 0)
vardict = dict(DBHOST = 'localhost')
for v in ('LOGNAME', 'DBHOST'):
    try:
        vardict[v] = os.environ[v]
    except KeyError:
        pass

class DBcredError(Exception):
    pass

class DBcred(object):
    """This class uses ConfigParse to read and optionally write a "ini" type file
    of database credentials.
    This can be ".dbcred.ini" in the current directory,
    ~/lib/dbcred.ini in "lib" of the user's home directory or
    /etc/dbcredi.ini
    We work in terms of tuples (host, dbname, user, password)""" 
    
    def __init__(self):
        global configfilepaths
        self.cparser = ConfigParser.SafeConfigParser()
        self.cparser.read(configfilepaths)

    def get(self, name):
        """Get credentials for the name"""
        try:
            return  (self.cparser.get(name, 'host', 0, vardict),
                     self.cparser.get(name, 'database', 0, vardict),
                     self.cparser.get(name, 'user', 0, vardict),
                     self.cparser.get(name, "password", 1))
        
        except ConfigParser.NoSectionError:
            raise DBcredError("Section " + name + " not known")
        except ConfigParser.NoOptionError:
            raise DBcredError("Section " + name + " not fully defined")
    
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

    