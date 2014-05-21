# For running program modules and feeding them interactive data

import subprocess
import os.path
import os
import copy

class ModelError(Exception):
    """Throw this if some error occurs running model"""
    pass

class ModelRunner(object):
    """Manage a subprocess object"""

    def __init__(self, programfile):
        pf = os.path.expanduser(programfile)
        self.program = pf
        self.envir = copy.copy(os.environ)
        self.dir = os.getcwd()
        self.proc = None

    def addenv(self, name, val):
        """Add environment variable to program environment"""
        self.envir[name] = val

    def delenv(self, name):
        """Remove environment variable from environment for program"""
        try:
            del self.envir[name]
        except KeyError:
            pass
    
    def setdir(self, dir):
        """Set starting dir appropriately"""
        self.dir = os.path.expanduser(dir)

    def go(self):
        """Set program running"""
        try:
            self.proc = subprocess.Popen([self.program], cwd=self.dir, env=self.envir, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except OSError as oe:
            raise ModelError("Error starting " + self.program + " - error was " + oe.args[1])
        pr = self.proc.poll()
        if pr is not None:
            raise ModelError("Startup error code " + str(pr) + " starting program")
        self.proginput = self.proc.stdin.fileno()
        self.progoutput = self.proc.stdout.fileno()

    def readout(self):
        """Read stuff from input (will block if none)"""
        return os.read(self.progoutput, 5000)

    def send(self, stuff):
        """Send data to program"""
        os.write(self.proginput, stuff + "\n")

