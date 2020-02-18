# Check designated object is within image with enough room round it

import numpy as np

def checkcoord(w, imagedata, radec, searchwidth, apwidth = 6):
    """Work out if given target is within image with enough room for search for actual object.

    Aargs are:

        w = parsed FITS header
        imagedata - Image data, don't actuallylook at this we just want the sizes
        radec - tuple with (RA, DEC) of object
        searchwidth - pixels we search either way
        apwidth - aperture width

    Returns:

        0 if no problem
        1 if RA and DEC within image but too close to edge for searchwidth
        2 if RA or DEC outside image"""

    pixrows, pixcols = imagedata.shape
    cornerpix = np.array(((0,0), (pixcols-1, 0), (0, pixrows-1), (pixcols-1, pixrows-1)), np.float)
    cornerradec = w.wcs_pix2world(cornerpix, 0)
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)
    raobj, decobj = radec
    if raobj <= ramin or raobj >= ramax: return 2
    if decobj <= decmin or decobj >= decmax: return 2
    cwidth = searchwidth + apwidth
    objx, objy = w.wcs_world2pix(np.array([radec]), 0).flatten()
    if objx <= cwidth or objx >= cwidth + pixcols: return 1
    if objy <= cwidth or objy >= cwidth + pixcols: return 1
    return 0
