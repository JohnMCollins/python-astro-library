# Use scipy/numpy to integrate over range and get mean value

import numpy as np
import scipy.integrate as si

def mean_value(rangev, xvalues, yvalues):
    """Get mean value by integration of y values

    First arg is datarange object
    Second argument is x values
    Third argument is y values"""

    sel = (xvalues >= rangev.lower) & (xvalues <= rangev.upper)
    sxv = xvalues[sel]
    integ = si.trapz(yvalues[sel], sxv)
    return integ / (sxv[-1] - sxv[0])

    
