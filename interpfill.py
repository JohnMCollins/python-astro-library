# Interpolate a pair of points at given point

def interpfill(indx, targx, xvals, yvals):

    """Generate a point by interpolation between indx and indx+1
    to give a target x value of targx and return (x, y)"""

    x0 = xvals[indx]
    x1 = xvals[indx+1]
    y0 = yvals[indx]
    y1 = yvals[indx+1]
    return (targx, y0 + ((y1 - y0)/(x1 - x0)) * (targx - x0))

def interpfille(indx, targx, xvals, yvals, yerrs):

    """Generate a point by interpolation between indx and indx+1
    to give a target x value of targx and return (x, y)
    Also compute errors"""

    x0 = xvals[indx]
    x1 = xvals[indx+1]
    y0 = yvals[indx]
    y1 = yvals[indx+1]
    e0 = yerrs[indx]
    e1 = yerrs[indx+1]
    return (targx, y0 + ((y1 - y0)/(x1 - x0)) * (targx - x0), (e0 + e1) / 2.0)
