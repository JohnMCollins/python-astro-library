# Find best coords of image locations

import numpy as np

def findimagelocs(imagedata, sign, apwidth = 6):
    """Find x,y coods and adus of objects in imagedate.
    
    imagedate = 2-D array for image giving ADUs subtract off median first if Requiredr
    sign - number of ADUs in aperture to be significant
    apwidth radius in pixels"
    
    return list of (x, y, adus)"""
    
    pixrows, pixcols = imagedata.shape
    
    mincol = apwidth
    maxcol = pixcols - apwidth - 1
    
    adiff = 2 * apwidth
    arng = adiff + 1
    apsq = apwidth * apwidth
    
    mask = np.zeros((arng, arng))
    rads = np.add.outer(np.arange(-apwidth,apwidth+1)**2,np.arange(-apwidth,apwidth+1)**2)
    mask[rads <= apsq] = 1.0
    
    results = []
    
    for srow in range(apwidth, pixrows-apwidth):
      
        crow = imagedata[srow]
        
        for place in np.where(crow > 0)[0]:
                      
            for xp in range(max(0, place-adiff), min(place,pixcols-arng)):
                
                adus = np.sum(imagedata[srow-apwidth:srow+apwidth+1,xp:xp+arng] * mask)
                if adus >= sign:
                    newres = (xp+apwidth, srow, adus)
                    if newres not in results:  
                        results.append(newres)

    results.sort(key=lambda x: x[2], reverse=True)
    
    skip = np.ones((len(results), ), dtype=np.bool)
       
    for firstp in range(0, len(results)):
        xf, yf, aduf = results[firstp]
        for nextp in range(firstp+1, len(results)):
            if not skip[nextp]: continue
            xn, yn, adun = results[nextp]
            if (xf-xn)**2 + (yf-yn)**2 <= apsq:
                skip[nextp] = False
    
    return np.array(results)[skip]
