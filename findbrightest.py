# Find the object nearest to the specified pixels.

import numpy as np

def findbrightest(imagedata, apsize = 6):
    """Find brightest object in array and return pixel coords
    
    Inputs:
        imagedata - 2d numpy array of imagedatga probably corrspos - (col, row) of starting cooridinates
        apsize - pixel radius of search aperture
    
    Outputs:
        (col, row, adus) of found object max in given area."""
        

    pixrows, pixcols = imagedata.shape
    
    masksz = apsize * 2 + 1
    
    ys = np.arange(-apsize, apsize+1).repeat(masksz).reshape(masksz, masksz) ** 2
    xs = ys.transpose()
    r2 = ys + xs
    mask = r2 <= apsize ** 2
    mask = mask.astype(np.float64)

    # Define the rectangle of search limits min is 0 in each case
    
    maxcol = pixcols - masksz
    maxrow = pixrows - masksz
  
    maxadus = -1e9
    col_max = -1
    row_max = -1
    
    for y in range(0,maxrow):
        ycent = y + apsize
        for x in range(0,maxcol):
            xcent = x + apsize
            adus = np.sum(imagedata[y:y+masksz,x:x+masksz] * mask)
            if adus < maxadus: continue
            maxadus = adus
            col_max = xcent
            row_max = ycent
    
    if col_max <= 0: return None
    return (col_max, row_max, maxadus)
