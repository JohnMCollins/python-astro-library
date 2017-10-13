# Get DB credentials from standard places

import ConfigParser
import os.path

class DBcred(object):
    
    def __init__(self):
        self.hostname = None
        self.dbname = None
        self.username = None
        self.password = None

    def get(self, name):
        """Get credentials for the name"""
        