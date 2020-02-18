# Routine for plotting grid on immages

import numpy as np
import matplotlib.pyplot as plt

def radecgridplt(w, dat, rg):

    """Plot RA/DEC grid on image.

        w is a "scscoord" structure
        dat is the immage
        rg is a remgemom structure"""

    if rg.divspec.nocoords:
        return

    # Get coords of edges of picture

    pixrows, pixcols = dat.shape
    cornerpix = ((0,0), (pixcols-1, 0), (9, pixrows-1), (pixcols-1, pixrows-1))
    cornerradec = w.pix_to_coords(cornerpix)
    isrotated = abs(cornerradec[0,0] - cornerradec[1,0]) < abs(cornerradec[0,0] - cornerradec[2,0])

    # Get matrix of ra/dec each pixel

    pixarray = np.array([[(x, y) for x in range(0, pixcols)] for y in range(0, pixrows)])
    pixcoords = w.pix_to_coords(pixarray.reshape(pixrows*pixcols,2)).reshape(pixrows,pixcols,2)
    ratable = pixcoords[:,:,0]
    dectable = pixcoords[:,:,1]
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)

    radivs = np.linspace(ramin, ramax, rg.divspec.divisions).round(rg.divspec.divprec)
    decdivs = np.linspace(decmin, decmax, rg.divspec.divisions).round(rg.divspec.divprec)

    ra_x4miny = []
    ra_y4minx = []
    ra_xvals = []
    ra_yvals = []
    dec_x4miny = []
    dec_y4minx = []
    dec_xvals = []
    dec_yvals = []

    for r in radivs:
        ra_y = np.arange(0, pixrows)
        diffs = np.abs(ratable-r)
        ra_x = diffs.argmin(axis=1)
        sel = (ra_x > 0) & (ra_x < pixcols-1)
        ra_x = ra_x[sel]
        ra_y = ra_y[sel]
        if len(ra_x) == 0: continue
        if ra_y[0] < rg.divspec.divthresh:
            ra_x4miny.append(ra_x[0])
            ra_xvals.append(r)
        if ra_x.min() < rg.divspec.divthresh:
            ra_y4minx.append(ra_y[ra_x.argmin()])
            ra_yvals.append(r)
        plt.plot(ra_x, ra_y, color=rg.divspec.racol, alpha=rg.divspec.divalpha)

    for d in decdivs:
        dec_x = np.arange(0, pixcols)
        diffs = np.abs(dectable-d)
        dec_y = diffs.argmin(axis=0)
        sel = (dec_y > 0) & (dec_y < pixrows-1)
        dec_x = dec_x[sel]
        dec_y = dec_y[sel]
        if len(dec_x) == 0: continue
        if dec_x[0] < rg.divspec.divthresh:
            dec_y4minx.append(dec_y[0])
            dec_yvals.append(d)
        if dec_y.min() < rg.divspec.divthresh:
            dec_x4miny.append(dec_x[dec_y.argmin()])
            dec_xvals.append(d)
        plt.plot(dec_x, dec_y, color=rg.divspec.deccol, alpha=rg.divspec.divalpha)

    fmt = '%.' + str(rg.divspec.divprec) + 'f'

    if isrotated:
        rafmt = [fmt % r for r in ra_yvals]
        decfmt = [fmt % d for d in dec_xvals]
        plt.yticks(ra_y4minx, rafmt)
        plt.xticks(dec_x4miny, decfmt)
        plt.ylabel('RA (deg)')
        plt.xlabel('Dec (deg)')
    else:
        rafmt = [fmt % r for r in ra_xvals]
        decfmt = [fmt % d for d in dec_yvals]
        plt.xticks(ra_x4miny, rafmt)
        plt.yticks(dec_y4minx, decfmt)
        plt.xlabel('RA (deg)')
        plt.ylabel('Dec (deg)')
