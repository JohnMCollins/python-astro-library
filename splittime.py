# Split plot into sets of subplots where time separation is given
# Assume that times are given as datetime.datetime

import datetime
import numpy as np

discrim = np.vectorize(lambda x: x.total_seconds())

def splittime(timearray, valuearray, separation):
    """Split plot given by first parameter (times) and second parameter (values)
    into array of sub-plots, separating the initial plot if the difference is >= separation in seconds"""
    
    diffs = np.diff(timearray)
    places = np.where(discrim(diffs) >= separation)[0] + 1
    
    ta = np.array(timearray)
    va = np.array(valuearray)
    
    results = []
    lastp = 0
    
    for p in places:
        nextt = ta[lastp:p]
        nextv = va[lastp:p]
        if len(nextt) > 1:
            results.append((nextt, nextv))
        lastp = p
    
    if lastp < len(ta) -1:
        results.append((ta[lastp:], va[lastp:]))
    
    return results
 