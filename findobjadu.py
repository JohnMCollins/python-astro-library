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
        
        Given ValueError if aperture > searchwidth
        
    Returns:
    
        None if it cannot find it
        tuple (pixx, pixy, adu)"""
    
    if apwidth > searchwidth:
        raise ValueError("findobjadvu: aperture > searchwidth")
    
    # Create matrix the same shape as imagedata with circular aperture radius apwidth centred
    # on the initial coords
    
    pixrows, pixcols = imagedata.shape
    cornerpix = np.array(((0,0), (pixcols-1, 0), (0, pixrows-1), (pixcols-1, pixrows-1)), np.float)
    cornerradec = w.wcs_pix2world(cornerpix, 0)
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)
    raobj, decobj = radec
    objx, objy = w.wcs_world2pix(np.array([radec]), 0).flatten()
    
    rads = np.sqrt(np.add.outer((np.arange(0,pixrows)-objy)**2,(np.arange(0,pixcols)-objx)**2))
    mask = np.zeros_like(imagedata)
    mask[rads <= apwidth] = 1.0
    
    return 0