# Fetch DoTS output data

import re
import string
import numpy

rep = re.compile("\s+")

class DOTSError(Exception):
    """Error in parsing file"""
    pass

def _dotsdata(fin, skiplines):
    result = []
    try:
        dims = [int(x) for x in rep.split(string.strip(fin.readline()))]
    except ValueError:
        raise DOTSError("Invalid integer fields in file")

    while len(dims) > 1 and dims[-1] == 1:
        dims.pop()

    # May have some extra bits to skip

    for n in range(0, skiplines):
        fin.readline()

    for line in fin:
        parts = rep.split(string.strip(line))
        try:
            parts = [float(x) for x in parts]
        except ValueError:
            raise DOTSError("Invalid float value in file")
        result.extend(parts)

    dims.reverse()
    return numpy.array(result).reshape(dims)

def dotsdata(f, skiplines=0):
    """Return array(s) from a DoTS output file

    f is either an open file or a string representing a file name
    skiplines gives a number of lines to skip after the first dims line"""

    if isinstance(f, str):
        try:
            fin = open(f)
        except IOError as e:
            raise DOTSError("IO error on " + f + " - ", e.args[1])
        try:
            return _dotsdata(fin, skiplines)
        except DOTSError:
            raise
        finally:
            fin.close()
    else:
        return _dotsdata(f, skiplines)
