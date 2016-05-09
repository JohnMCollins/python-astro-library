# Equivalent width calc

import scipy.integrate as si
import numpy as np
import interpfill

def equivalent_width(range, xvalues, yvalues, interpolate = False, absorb = False):
    """Calculate equivalent width by integration.

    Assumes continuum normalised.
    Args are range (datarange object) and lists of x values and yvalues"""

    lowend, highend = np.searchsorted(xvalues, (range.lower, range.upper))
    selx = xvalues[lowend:highend]
    sely = yvalues[lowend:highend]
    if interpolate and lowend > 0 and highend < len(xvalues) - 1:
        if xvalues[lowend] != range.lower:
            x, y = interpfill.interpfill(lowend, range.lower, xvalues, yvalues)
            selx = np.concatenate(((x,), selx))
            sely = np.concatenate(((y,), sely))
        if xvalues[highend] != range.upper:
            x,y, = interpfill.interpfill(highend, range.upper, xvalues, yvalues)
            selx = np.concatenate((selx, (x,)))
            sely = np.concatenate((sely, (y,)))
    ret = si.trapz(sely, selx) - (max(selx) - min(selx))
    if absorb:
        return -ret
    return  ret

def equivalent_width_err(range, xvalues, yvalues, yerrs, interpolate = False, absorb = False):
    """Calculate equivalent width by integration and also error term.
    
    Assumes continuum normalised.
    Args are range (datarange object) and lists of x values, yvalues and yerrs"""
    
    lowend, highend = np.searchsorted(xvalues, (range.lower, range.upper))
    selx = xvalues[lowend:highend]
    sely = yvalues[lowend:highend]
    yes = yerrs[lowend:highend]
    if interpolate and lowend > 0 and highend < len(xvalues) - 1:
        if xvalues[lowend] != range.lower:
            x, y, e = interpfill.interpfille(lowend, range.lower, xvalues, yvalues, yerrs)
            selx = np.concatenate(((x,), selx))
            sely = np.concatenate(((y,), sely))
            yes = np.concatenate(((e,), yes))
        if xvalues[highend] != range.upper:
            x, y, e = interpfill.interpfille(highend, range.upper, xvalues, yvalues, yerrs)
            selx = np.concatenate((selx, (x,)))
            sely = np.concatenate((sely, (y,)))
            yes = np.concatenate((yes, (e,)))
    wid = max(selx) - min(selx)
    ret = si.trapz(sely, selx) - wid
    rete = np.sqrt(np.sum(np.square(yes))) * wid 
    if absorb:
        return (-ret, rete)
    return  (ret, rete)