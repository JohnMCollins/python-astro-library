"""Match find results to object locations"""

import numpy as np


class FindError(Exception):
    """Raise this if we get problems with finding things"""


def allocate_locs(locresults, findresults, threshold=20.0, nocheck=False):
    """Attempt to allocate locations and results theshold gives limit in aresec we don't consider it matching in"""

    # build cross-table of locations by row and find results by column giving distances as a complex
    # with RA in the real part and DEC in the imageinary part

    ctab = np.subtract.outer([complex(l.ra, 2 * l.dec) for l in locresults.results()], [complex(f.radeg, 2 * f.decdeg) for f in findresults.results()])

    # We put target as first result in locresults so start from there
    # targloc = locresults.resultlist[0]

    # Get index of nearest to target (there might be equals but the find results are ordered as brightest first
    # and we assume target is amongst brightest)

    # Convert threhold to degrees

    dthreshold = threshold / 3600.0

    # assume that nearest to target coords is target

    displ = ctab[0, abs(ctab[0]).argmin()]

    if abs(displ) > dthreshold:
        raise FindError("Could not find target within {:.3g} arcsec".format(threshold))

    # Relocate evergything to actual coords of target

    updctab = ctab - displ
    absupdctab = abs(updctab)
    sorted_dists = absupdctab.flatten()
    sorted_dists = sorted_dists[sorted_dists <= dthreshold]
    sorted_dists.sort()

    rtab = []

    for d in sorted_dists:
        rlist, clist = np.where(absupdctab == d)
        for r, c in zip(rlist, clist):
            rtab.append((r, c, d))

    if nocheck:
        return rtab

    hadcols = [p[1] for p in rtab]
    scols = set(hadcols)

    if len(hadcols) != len(set(hadcols)):
        newrtab = []
        for row, col, dist in rtab:
            if col not in scols:
                continue
            rows = [c[0] for c in rtab if c[1] == col]
            if len(rows) != 1:
                dists = np.array([c[2] for c in rtab if c[1] == col])
                am = dists.argmin()
                newrtab.append((rows[am], col, dists[am]))
            else:
                newrtab.append((row, col, dist))
            scols.discard(col)
        rtab = newrtab

    hadrows = [p[0] for p in rtab]
    srows = set(hadrows)

    if len(hadrows) != len(srows):
        newrtab = []
        for row, col, dist in rtab:
            if row not in srows:
                continue
            cols = [r[1] for r in rtab if r[0] == row]
            if len(cols) != 1:
                dists = np.array([r[2] for r in rtab if r[0] == row])
                am = dists.argmin()
                newrtab.append((row, cols[am], dists[am]))
            else:
                newrtab.append((row, col, dist))
            srows.discard(row)
        return  newrtab
    return rtab
