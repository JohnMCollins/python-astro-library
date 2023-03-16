"""Routines for logging and error exit"""

import sys
import fcntl
import os.path

class Logging:
    """Claass for log entries"""

    def __init__(self, logfile = None, filename = None):

        self.outfile = sys.stderr
        self.filename = filename    # Prefix for messages
        self.logfilename = None
        if logfile is not None:
            self.outfile = None #Don't want to open it yet to avoid creating empty files
            self.logfilename = os.path.abspath(logfile) # Insulation against directory changes

    def checkopen(self):
        """Check if log file is open and if not open it"""
        if self.outfile is None:
            try:
                self.outfile = open(self.logfilename, "a+")
            except IOError as e:
                print("Panic cannot open logfile", self.logfilename, "error was", e.args[1], file=sys.stderr)
                sys.exit(255)

    def write(self, *args):
        """Write message to log making sure we flush"""
        self.checkopen()
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
