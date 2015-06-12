# Fixes to get argrelmax and argrelmin doing it properly

import numpy as np
import scipy.signal as ss

def rewrite_equal(wls, amps):
    """ss.argrelmax and ss.argrelmin don't work very well (at all) if there are equal value
    amplitudes, so we rewrite amplitudes which are equal by fitting the points in question
    and the two either side to a quadratic and replacing the values"""

    tamps = amps.copy()
    la = len(tamps)
    zeroinds = np.where(tamps[0:la-1] == tamps[1:la])[0]
    zeroinds = zeroinds[(zeroinds > 1) & (zeroinds < la-1)]
    for zi in zeroinds:
        wlseg = wls[zi-1:zi+3]
        ampseg = tamps[zi-1:zi+3]
        c = np.polyfit(wlseg, ampseg, 2)
        tamps[zi:zi+2] = np.polyval(c, wlseg[1:3])
    return tamps

def argrelmax(wls, amps):
    """Do argrelmax but fit a quadaratic where necessary to avoid problems with straddling a maximum"""

    return  ss.argrelmax(rewrite_equal(wls, amps))[0]

def argrelmin(wls, amps):
    """Do argrelmin but fit a quadaratic where necessary to avoid problems with straddling a maximum"""

    return  ss.argrelmin(rewrite_equal(wls, amps))[0]

def maxmaxes(wls, amps):
    """Return maxima in descending sorted order of value"""
    maxes = argrelmax(wls, amps)
    order = np.argsort(-amps[maxes])
    return maxes[order]

def minmins(wls, amps):
    """Return minima in ascending sorted order of value"""
    maxes = argrelmin(wls, amps)
    order = np.argsort(amps[maxes])
    return maxes[order]
