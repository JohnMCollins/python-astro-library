# Find best coords of image locations

import numpy as np


def tooclose(row, col, existing):
    """Reject possible if too close to existing one"""

    global apsq

    for r, c, adu in existing:
        if (r - row) ** 2 + (c - col) ** 2 <= 4 * apsq:
            return True
    return False


def findfast(imagedata, sign, apwidth=6):
    """Find x,y coods and adus of objects in imagedate.

    This version tries to do it all at once using a 4-day array of masks.
    imagedate = 2-D array for image giving ADUs subtract off median first if Requiredr
    sign - starting from points great than this * std dev away
    apwidth radius in pixels"

    return list of (x, y, adus)"""

    global apsq

    pixrows, pixcols = imagedata.shape

    apdiam = 2 * apwidth + 1
    apsq = apwidth ** 2
    mincol = minrow = apwidth - 1
    maxrow = pixrows - apdiam  # This is actually 1 more
    maxcol = pixcols - apdiam  # This is actually 1 more

    # Kick off with masj ub bottom left

    mask = np.zeros_like(imagedata)
    rads = np.add.outer((np.arange(0, pixrows) - apwidth) ** 2, (np.arange(0, pixcols) - apwidth) ** 2)
    rv, cv = np.where(rads <= apsq)
    for r, c in zip(rv, cv):
        mask.itemset((r, c), 1.0)
    points = np.sum(mask)

    # Get list of points greater than n std devs within search area

    flatim = imagedata[minrow:maxrow, mincol:maxcol].flatten()
    flatim = flatim[flatim > flatim.mean() + sign * flatim.std()]
    flatim = -np.unique(-flatim)

    rows = []
    cols = []
    sums = []

    for mxv in flatim:
        wr, wc = np.where(imagedata == mxv)
        for r, c in zip(wr, wc):
            if r < minrow or r >= maxrow:
                continue
            if c < mincol or c >= maxcol:
                continue
            rows.append(r)
            cols.append(c)
            sums.append(np.sum(np.roll(np.roll(mask, shift=c - mincol, axis=1), shift=r - minrow, axis=0) * imagedata))

    possibles = [ (rows[n], cols[n], sums[n]) for n in (-np.array(sums)).argsort() ]

    results = []
    for r, c, adu in possibles:
        if tooclose(r, c, results):
            continue
        results.append((r, c, adu))
    return sorted(results, key=lambda x:x[2], reverse=True)
