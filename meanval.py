# Use scipy/numpy to integrate over range and get mean value

import numpy as np
import math
import scipy.integrate as si
import interpfill

def mean_value(rangev, xvalues, yvalues, yerrs = None, interpolate = False):
    """Get mean value by integration of y values

    First arg is datarange object
    Second argument is x values
    Third argument is y values
    Return tuple with x range and integration result"""

    lowend, highend = np.searchsorted(xvalues, (rangev.lower, rangev.upper))
    selx = xvalues[lowend:highend]
    sely = yvalues[lowend:highend]

    # Don't do any interpolation stuff if the range isn't entirely within the values

    if interpolate and lowend > 0 and highend < len(xvalues) - 1:

        if xvalues[lowend] != rangev.lower:

            x, y = interpfill.interpfill(lowend, rangev.lower, xvalues, yvalues)
            selx = np.concatenate(((x,), selx))
            sely = np.concatenate(((y,), sely))

        if xvalues[highend] != rangev.upper:

            x,y, = interpfill.interpfill(highend, rangev.upper, xvalues, yvalues)
            selx = np.concatenate((selx, (x,)))
            sely = np.concatenate((sely, (y,)))

    integ = si.trapz(sely, selx)
    wid = max(selx) - min(selx)
    if yerrs is None:
        return (wid, integ)
    rete = math.sqrt(np.sum(np.square(yerrs[lowend:highend]))) * wid
    return (wid, integ, rete)
