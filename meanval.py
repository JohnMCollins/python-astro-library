# Use scipy/numpy to integrate over range and get mean value

import numpy as np
import math
import scipy.integrate as si

def mean_value(rangev, xvalues, yvalues, yerrs = None, interpolate = False):
    """Get mean value by integration of y values

    First arg is datarange object
    Second argument is x values
    Third argument is y values
    Return tuple with x range and integration result"""

    if yerrs is None:
        if interpolate:
            selx, sely = rangev.select_interpolate(xvalues, yvalues)
        else:
            selx, sely = rangev.select(xvalues, yvalues)
    else:
        if interpolate:
            selx, sely, sele = rangev.select_interpolate(xvalues, yvalues, yerrs)
        else:
            selx, sely, sele = rangev.select(xvalues, yvalues, yerrs)

    integ = si.trapz(sely, selx)
    wid = max(selx) - min(selx)
    if yerrs is None:
        return (wid, integ)
    rete = math.sqrt(np.sum(np.square(sele))) * wid
    return (wid, integ, rete)
