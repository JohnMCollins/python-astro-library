# Equivalent width calc

import scipy.integrate as si

def equivalent_width(range, xvalues, yvalues, absorb = False):
    """Calculate equivalent width by integration.

    Assumes continuum normalised.

    Args are range (datarange object) and lists of x values and yvalues"""

    xvals, yvals = range.select(xvalues, yvalues)

    ret = si.trapz(yvals, xvals) - (max(xvals) - min(xvals))
    if absorb:
        return -ret
    return  ret