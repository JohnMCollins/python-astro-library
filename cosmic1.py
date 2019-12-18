# First cut at cosmic elimination

import numpy as np
from networkx.classes.function import neighbors

def neighbix(r, c):
    """Check neighbours of maximum point all at sky level and blast the central point if so.
    return True if something done, false otherwise"""
    
    global crit, resultimage
    
    neighbs = np.concatenate((resultimage[r-1,c-1:c+2],[resultimage[r,c-1],resultimage[r,c+1]],resultimage[r+1,c-1:c+2]))
    if np.count_nonzero(neighbs > crit) != 0: return False
    resultimage[r,c] = np.median(neighbs)
    return True
    
def cosmic1(imagedata, sign = 2.0, hival = 10.0):
    """First cut at eliminating cosmics by knocking out spikes where the 8 immediate neightours are
    within the sky level). Sign gives the number of standard deviations to conside points
    to be within the sky leve.
    hival gives the limit of maxima to look forl"""
    
    global crit, resultimage
     
    pixrows, pixcols = imagedata.shape
    maxrow = pixrows - 1
    maxcol = pixcols - 1
    
    meanv = imagedata.mean()
    stdv = imagedata.std()
    crit = meanv + sign * stdv
    hv = meanv + hival * stdv
    
    resultimage = imagedata.copy()
    ndone = 0
    
    # Get list of points greater than n std devs within search area
    
    flatim = imagedata.flatten()
    flatim = flatim[flatim > hv]
    flatim = - np.unique(-flatim)
        
    for mxv in flatim:       
        wr, wc = np.where(imagedata == mxv)
        for r, c in zip(wr, wc):
            if r <= 0 or r >= maxrow:
                continue
            if c <= 0 or c >= maxcol:
                continue
            if neighbix(r, c):
                ndone += 1
    
    return (resultimage, ndone)