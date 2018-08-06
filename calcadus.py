# Calculati ADUs with given aperture radius at given coords

import numpy as np

class calcaduerror(Exception):
    """Throw this error if we hit the boundaries"""
    pass

def calcadus(imagedata, errorarray, objpixes, apsize = 6):
    """Calculate ADUs with given aperture radius.
    
    Inputs:
        imagedata - 2d numpy array of imagedatga
        arrorarray = corresponding errors
        objpixes 0th element column 1st element row
        apsize - pixel radius of search aperture
    
    Outputs:
        (nadus, error)"""
        

    objcol = objpixes[0]
    objrow = objpixes[1]
    pixrows, pixcols = imagedata.shape
    
    if objcol - apsize < 0 or objcol + apsize >= pixcols:
        raise calcaduerror("column too close to edge")
    if objrow - apsize < 0 or objrow + apsize >= pixrows:
        raise calcaduerror("column too close to edge")
    
    masksz = apsize * 2 + 1
    
    ys = np.arange(-apsize, apsize+1).repeat(masksz).reshape(masksz, masksz) ** 2
    xs = ys.transpose()
    r2 = ys + xs
    mask = r2 <= apsize ** 2
    count = float(np.sum(mask))
    mask = mask.astype(np.float64)
    adus = np.sum(imagedata[objrow-apsize:objrow+apsize+1,objcol-apsize:objcol+apsize+1] * mask)
    errs = np.sum((errorarray[objrow-apsize:objrow+apsize+1,objcol-apsize:objcol+apsize+1] * mask) ** 2)
    return (adus, errs / count)
