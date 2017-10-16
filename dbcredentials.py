# Get DB credentials from standard places

import ConfigParser
import os.path

class DBcred(object):
    
    def __init__(self):
        self.cparser = ConfigParser.SafeConfigParser()
        self.cparser.read(("/etc/dbcred.ini", os.path.expanduser("~/lib/dbcred.ini"), '.dbcred.ini'))

    def get(self, name):
        """Get credentials for the name"""
        