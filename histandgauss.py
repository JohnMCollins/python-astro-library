# Use plotting library to display histogram and overplat gaussian

import string
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as ss

def histandgauss(values, bins=20, colour='blue', histalpha=0.8, plotalpha=1.0, asperc=False):
    """Display histogram with given number of bins and colour and overplotted gaussian"""

    if isinstance(colour, str):
        colour = string.split(colour, ',')

    if asperc:
        scale = 100.0 / len(values)
        freqs, sizes, patches = plt.hist(values, bins=bins, color=colour[0], alpha=histalpha, weights=np.ones_like(values) * scale)
    else:
        scale = 1.0
        freqs, sizes, patches = plt.hist(values, bins=bins, color=colour[0], alpha=histalpha)

    resc = np.sum(freqs * np.diff(sizes))

    mv = values.mean()
    stv = values.std()

    # Redo that in case not much hist
    smoothsizes = np.linspace(sizes.min(), sizes.max(), 500)

    gsv = ss.norm.pdf(smoothsizes, loc=mv, scale=stv) * resc
    plt.plot(smoothsizes, gsv, color=colour[-1], alpha=plotalpha)
