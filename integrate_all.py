#integrate all spectra in a directory

import glob
import specplot
import numpy as np

def integrate_all(dir = "", suffix = '.fakespec'):
    """Produce a results table of complete integration of the spectra in the given files"""
    results = []
    fnames = dir
    if len(dir) != 0:
        dir += '/'
    glist = glob.glob(dir + '*' + suffix)
    for g in glist:
        spp = specplot.Specplot()
        spp.loadfile(g)
        results.append(np.trapz(spp.intensities))
    return  results

