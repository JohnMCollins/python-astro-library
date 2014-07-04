# Calculate tick values for plots.

import math
import numpy as np

def calcticks(size, mn, mx):
    """Calculate ticks and return a tuple of tick values and labels
       Args are size of plot, min and max"""
    rng = float(mx - mn)
    step = rng / size
    prec = int(-math.floor(math.log10(step)))
    step = round(step, prec)
    tv = np.arange(mn, mx+step, step)
    if prec <= 0:
        tvt = map(lambda x: "%d" % round(x), tv)
    else:
        fmt = "%%.%df" % prec
        tvt = map(lambda x: fmt % x, tv)
    return  (tv, tvt)

