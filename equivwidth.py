# Equivalent width calc

import scipy.integrate as si
import numpy as np

def equivalent_width(range, xvalues, yvalues, interpolate = False, absorb = False):
    """Calculate equivalent width by integration.

    Assumes continuum normalised.
    Args are range (datarange object) and lists of x values and yvalues"""

    if interpolate:
        selx, sely, sele = range.select_interpolate(xvalues, yvalues)
    else:
        selx, sely = range.select(xvalues, yvalues)
    ret = si.trapz(sely, selx) - (max(selx) - min(selx))
    if absorb:
        return -ret
    return  ret

def equivalent_width_err(range, xvalues, yvalues, yerrs, interpolate = False, absorb = False):
    """Calculate equivalent width by integration and also error term.

    Assumes continuum normalised.
    Args are range (datarange object) and lists of x values, yvalues and yerrs"""

    if interpolate:
        selx, sely, yes = range.select_interpolate(xvalues, yvalues, yerrs)
    else:
        selx, sely, yes = range.select(xvalues, yvalues, yerrs)
    wid = max(selx) - min(selx)
    ret = si.trapz(sely, selx) - wid
    rete = np.sqrt(np.sum(np.square(yes))) * wid
    if absorb:
        return (-ret, rete)
    return  (ret, rete)