# Match find results to object locations

import numpy as np


class FindError(Exception):
    """Raise this if we get problems with finding things"""

    def __init__(self, msg, rmsg=None, cmsg=None):

        super(FindError, self).__init__(self, msg, rmsg, cmsg)


def allocate_locs(locresults, findresults, threshold=20.0):
    """Attempt to allocate locations and results theshold gives limit in aresec we don't consider it matching in"""

    # build cross-table of locations by row and find results by column giving distances as a complex
    # with RA in the real part and DEC in the imageinary part

    ctab = np.subtract.outer([complex(l.radeg, l.decdeg) for l in locresults.results()], [complex(f.radeg, f.decdeg) for f in findresults.results()])

    # We put target as first result in locresults so start from there

    targloc = locresults.resultlist[0]

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

    hadrows = [p[0] for p in rtab]
    hadcols = [p[1] for p in rtab]
    srows = set(hadrows)
    scols = set(hadcols)
    if len(hadrows) != len(srows) or len(hadcols) != len(scols):
        dupr = []
        dupc = []
        for r in hadrows:
            if r not in srows:
                dupr.append(r)
            srows.dicard(r)
        for c in hadcols:
            if c not in scols:
                dupc.append(c)
            scols.discard(c)
        dupr.sort()
        dupc.sort()
        if len(dupr) != 0:
            if len(dupc) != 0:
                raise FindError("Duplicated rows and columns", dupr, dupc)
            raise FindError("Duplicated rows", dupr)
        else:
            raise FindError("Duplicated cols", None, dupc)
    return rtab
