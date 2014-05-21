# Fetch DoTS output data

import re
import string
import numpy

rep = re.compile("\s+")

class DOTSError(Exception):
    """Error in parsing file"""
    pass

def _dotsdata(fin):
    result = []
    try:
        dims = map(lambda x:int(x), rep.split(string.strip(fin.readline())))
    except ValueError:
        raise DOTSError("Invalid integer fields in file")

    while len(dims) > 1 and dims[-1] == 1:
        dims.pop()

    for line in fin:
        parts = rep.split(string.strip(line))
        try:
            parts = map(lambda x:float(x),parts)
        except ValueError:
            raise DOTSError("Invalid float value in file")
        result.extend(parts)

    dims.reverse()
    return numpy.array(result).reshape(dims)

def dotsdata(f):
    """Return array(s) from a DoTS output file

    f is either an open file or a string representing a file name"""

    if isinstance(f, str):
        try:
            fin = open(f)
        except IOError as e:
            raise DOTSError("IO error on " + f + " - ", e.args[1])
        try:
            return _dotsdata(fin)
        except DOTSError:
            raise
        finally:
            fin.close()
    else:
        return _dotsdata(f)

