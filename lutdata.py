# Fetch LUT output data

import re
import string
import numpy

rep = re.compile("\s+")

class LUTError(Exception):
    """Error in parsing file"""
    pass

class Lutdata(object):
    """Representation of LUT file for DoTS"""

    def __init__(self):
        self.ntemps = 1
        self.nlimbs = 1
        self.nvels = 1
        self.langles = None
        self.dataarray = None
        self.mint4 = 0.
        self.maxt4 = 0.
        self.minv = 0.
        self.maxv = 0.
        self.minla = 0.
        self.maxla = 0.

    def _loaddata(self, fin):
        """Guts of loading file of data from opened file"""

        # Get dimensions from first line

        try:
            dims = map(lambda x:int(x), rep.split(string.strip(fin.readline())))
        except ValueError:
            raise LUTError("Invalid integer fields in file")

        # Expecting 3 dims

        if len(dims) != 3:
            raise LUTError("Expecting dimensions to be 3 but found " + str(len(dims)))

        self.ntemps, self.nvels, self.nlimbs = dims
        dims.reverse()

        # Get data from second line

        try:
            line2 = map(lambda x:float(x), rep.split(string.strip(fin.readline())))
        except ValueError:
            raise LUTError("Invalid float fields in file")

        if len(line2) != 6:
            raise LUTError("Expecting second line of file to have 6 fields but found " + str(len(line2)))

        self.mint4, self.maxt4, self.minv, self.maxv, self.minla, self.maxla = line2

        # Slurp up rest of data in one swell foop

        try:
            arr = numpy.loadtxt(fin)
        except ValueError:
            raise LUTError("Invalid float fields in LUT file")

        # Check we've got what we expect

        npoints = reduce(lambda x,y:x*y,dims)
        if  len(arr) != npoints + self.nlimbs:
            raise LUTError("Expecting " + str(npoints + self.nlimbs) + " but read " + str(len(arr)))

        self.langles = arr[0:self.nlimbs]
        arr = arr[self.nlimbs:]
        arr = arr.reshape(dims)
        self.dataarray = arr.transpose()

    def loaddata(self, f):
        """Return array(s) from a LUT output file

        f is either an open file or a string representing a file name"""

        if isinstance(f, str):
            try:
                fin = open(f)
            except IOError as e:
                raise LUTError("IO error on " + f + " - ", e.args[1])
            try:
                return self._loaddata(fin)
            except LUTError:
                raise
            finally:
                fin.close()
        else:
            return self._loaddata(f)
