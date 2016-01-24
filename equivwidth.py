# Equivalent width calc

import scipy.integrate as si
import numpy as np

def equivalent_width(range, xvalues, yvalues, absorb = False):
    """Calculate equivalent width by integration.

    Assumes continuum normalised.

    Args are range (datarange object) and lists of x values and yvalues"""

    xvals, yvals = range.select(xvalues, yvalues)

    ret = si.trapz(yvals, xvals) - (max(xvals) - min(xvals))
    if absorb:
        return -ret
    return  ret

def equivalent_width_err(range, xvalues, yvalues, yerrs, absorb = False):
    """Calculate equivalent width by integration and also error term.
    
    Assumes continuum normalised.

    Args are range (datarange object) and lists of x values, yvalues and yerrs"""
    
    xvals, yvals, yes = range.select(xvalues, yvalues, yerrs)

    wid = max(xvals) - min(xvals)
    ret = si.trapz(yvals, xvals) - wid
    rete = np.sqrt(np.sum(np.square(yes))) * wid 
    if absorb:
        return (-ret, rete)
    return  (ret, rete)