# Scan image file in vicinity of specified coords

import numpy as np

def findobjadu(w, imagedata, radec, searchwidth, apwidth = 6):
    """Find object in image file in vicinity of given coords
    
    Aargs are:
    
        w = parsed FITS header
        imagedata - Image data, don't actuallylook at this we just want the sizes
        radec - tuple with (RA, DEC) of object
        searchwidth - pixels we search either way
        apwidth (default 6) aperture dith - using circular aperture
        
        We should have already checked we can accommodate search and apertgure width
        
    Returns:
    
        None if it cannot find it
        tuple (pixx, pixy, adu)"""

    
    # Create matrix the same shape as imagedata with circular aperture radius apwidth centred
    # on the initial coords
    
    pixrows, pixcols = imagedata.shape
    cornerpix = np.array(((0,0), (pixcols-1, 0), (0, pixrows-1), (pixcols-1, pixrows-1)), np.float)
    cornerradec = w.wcs_pix2world(cornerpix, 0)
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)
    raobj, decobj = radec
    objx, objy = w.wcs_world2pix(np.array([radec]), 0).flatten().round()
    
    rads = np.sqrt(np.add.outer((np.arange(0,pixrows)-objy)**2,(np.arange(0,pixcols)-objx)**2))
    mask = np.zeros_like(imagedata)
    mask[rads <= apwidth] = 1.0
    
    med = np.median(imagedata)
    redimage = np.clip(imagedata - med, 0, None)
    
    swsq = searchwidth * searchwidth
    adulist = []
    coordlist = []
    dists = []
    for yr in range(-searchwidth-1, searchwidth + 1):
        ysq = yr * yr
        for xr in range(-searchwidth-1, searchwidth + 1):
            xsq = xr * xr
            dist = xsq + ysq
            if dist > swsq:
                continue
            rmask = np.roll(mask, (-yr, -xr), (0,1))
            adulist.append(np.sum(redimage * rmask))
            coordlist.append((objx+xr, objy+yr))
            dists.append(dist)
    
    # Find the maximum ADU - if more than one fit the bill, take the closest
    # maybe we want a weighting?
    
    mx = max(adulist)
    if mx <= 0.0: return None
    adulist = np.array(adulist)
    coordlist = np.array(coordlist)
    dists = np.array(dists)
    whind = np.where(adulist >= mx)[0]
    if len(whind) == 1:
        picked = whind[0]
    else:
        adulist = adulist[whind]
        coordlist = coordlist[whind]
        dists = dists[whind]
        picked = dists.argmin()
        
    return (coordlist[picked,0], coordlist[picked,1], adulist[picked])