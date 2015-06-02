# Split plot into sets of subplots where time separation is given
# Assume that times are given as datetime.datetime

import datetime
import numpy as np

discrim = np.vectorize(lambda x: x.total_seconds())

def splittime(separation, timearray, *valuearrays):
    """This routine is for splitting a set of arrays all of the same size into an array of arrays
       designating different periods split where the time differences exceed a given time in seconds.
       The argument timearray is assumed to be a datefime object.
       The final argument gives the other arrays (nb vaiadic)"""
    
    diffs = np.diff(timearray)
    places = np.where(discrim(diffs) >= separation)[0] + 1
      
    ta = np.array(timearray)
    va = np.array(valuearrays)
    
    results = []
    lastp = 0
    
    for p in places:
        nextt = ta[lastp:p]
        nextv = list(va[:,lastp:p])
        if len(nextt) > 1:
            nextv.insert(0,nextt)
            results.append(nextv)
        lastp = p
    
    if lastp < len(ta) -1:
        nextv = list(va[:,lastp:])
        nextv.insert(0, ta[lastp:])
        results.append(nextv)
    
    return results
 