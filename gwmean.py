"""Calculate weighted mean with error"""

import numpy as np
import math


def wgmean(values, errs):
    """Calculate weighted geometric mean of given values and error as tuple"""
    
    # if len(values) != len(errs):
    #    raise ValueError("Expecting lengths of values and errors to be the same")
    
    values = np.array(values)
    errs = np.array(errs)
    weights = 1.0 / errs
    sumweights = np.sum(weights)
    gm = np.exp(np.sum(np.log(values) * weights) / sumweights)
    siggm = gm / sumweights * math.sqrt(np.sum(values ** -2.0))
    return (gm, siggm)
