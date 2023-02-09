"""Routines for logging and error exit"""

import sys
import fcntl

class Logging:
    """Claass for log entries"""

    def __init__(self, logfile = None, filename = None):

        self.outfile = sys.stderr
        self.filename = None
        if logfile is not None:
            self.outfile = open(logfile, "a+")

    def write(self, *args):
        """Write message to log making sure we flush"""
        fcntl.lockf(self.outfile, fcntl.LOCK_EX)
        if self.filename is not None and len(self.filename) != 0:
            print(self.filename, ": ", sep='', end='', file=self.outfile)
        print(*args, file=self.outfile)
        self.outfile.flush()
        fcntl.lockf(self.outfile, fcntl.LOCK_UN)

    def set_filename(self, fname):
        """Set filename for prefix of each line"""
        self.filename = fname

    def die(self, ecode, *args):
        """Die after writing log"""
        self.write(*args)
        sys.exit(ecode)

def parseargs(argp):
    """Option to parse argument for logging"""
    argp.add_argument('--logfile', type=str, help='File for log output if not stderr')

def getargs(resargs):
    """Get argument and return logging structure"""
    return  Logging(resargs['logfile'])
