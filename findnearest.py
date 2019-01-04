# Find the object nearest to the specified pixels.

import numpy as np

def findnearest(imagedata, spos, apsize = 6, searchrad = 15, minadus = -1):
    """Find nearest object in array nearest to given coordinates
    
    Inputs:
        imagedata - 2d numpy array of imagedatga probably corrected for flat/bias
        spos - (col, row) of starting cooridinates
        apsize - pixel radius of search aperture
        searchrad - radius to search in in pixels. Probably biggesr that psize but doesn't have to be.
    
    Outputs:
        (col, row, adus) of found object max in given area."""
        

    pixrows, pixcols = imagedata.shape
    
    # Get column and row to start without requiring spos to be a 2-element thing
    
    scol = int(round(spos[0]))
    srow = int(round(spos[1]))
    
    masksz = apsize * 2 + 1
    
    ys = np.arange(-apsize, apsize+1).repeat(masksz).reshape(masksz, masksz) ** 2
    xs = ys.transpose()
    r2 = ys + xs
    mask = r2 <= apsize ** 2
    mask = mask.astype(np.float64)

    # Define the rectangle of search limits
    
    mincol = max(0, scol - searchrad - apsize)
    maxcol = min(pixcols, scol + searchrad + apsize + 1) - masksz
    minrow = max(0, srow - searchrad - apsize)
    maxrow = min(pixrows, srow + searchrad + apsize + 1) - masksz
  
    sr2 = searchrad ** 2
    
    maxadus = minadus * np.sum(mask)
    maxradsq = 10000000000
    col_max = -1
    row_max = -1
    
    for y in range(minrow,maxrow):
        ycent = y + apsize
        y2 = (ycent - srow) ** 2
        for x in range(mincol,maxcol):
            xcent = x + apsize
            x2 = (xcent - scol) ** 2
            r2 = x2 + y2
            if r2 > sr2: continue
            adus = np.sum(imagedata[y:y+masksz,x:x+masksz] * mask)
            if adus < maxadus: continue
            if adus == maxadus and r2 >= maxradsq: continue
            maxadus = adus
            col_max = xcent
            row_max = ycent
            maxradsq = r2
    
    if col_max <= 0: return None
    return (col_max, row_max, maxadus)
