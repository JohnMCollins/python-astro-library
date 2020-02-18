# Right ascension and declination conversions

import string
import math
from functools import reduce

class RADconvError(Exception):
    pass

def ra_hr2deg(ra):
    """Convert RA in hours (possibly string) to degrees"""
    try:
        return ra * 15.0
    except TypeError:
        bits = string.split(ra, ':')
        if len(bits) != 3:
            raise RADconvError("Expecting 3-part RA string")
        try:
            return  reduce(lambda a, b: a*60.0 + b, [float(c) for c in bits]) / 240.0
        except TypeError:
            raise RADconvError("Invalid RA string " + ra)


def ra_deg2hr(ra, asstr = False):
    """Convert RA in degrees to hours or as string if asstr is true"""
    if asstr:
        ra /= 15.0
        h = int(math.floor(ra))
        ra = (ra - h) * 60
        m = int(math.floor(ra))
        ra = (ra - m) * 60
        return  "%.2d:%.2d:" % (h, m) + ("%.2f" % (ra + 100.))[1:]
    return ra / 15.0


def dec2float(dec):
    """Convert declination string to float"""
    sig = 1.0
    if dec[0] == '-':
        dec = dec[1:]
        sig = -1.0
    bits = string.split(dec, ':')
    if len(bits) != 3:
            raise RADconvError("Expecting 3-part DEC string")
    try:
        return math.copysign(reduce(lambda a, b: a*60.0 + b, [float(c) for c in bits]), sig) / 3600.0
    except TypeError:
        raise RADconvError("Invalid DEC string " + dec)

def dec2str(dec):
    """Convert declination flat to string"""
    sig = ""
    if dec < 0.0:
        dec = - dec
        sig = "-"
    d = int(math.floor(dec))
    dec = (dec - d) * 60
    m = int(math.floor(dec))
    dec = (dec - m) * 60
    return  sig + "%.2d:%.2d:" % (d, m) + ("%.2f" % (dec + 100.))[1:]