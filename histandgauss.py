# Use plotting library to display histogram and overplat gaussian

import string
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as ss

def histandgauss(values, bins=20, colour='blue', histalpha=0.8, plotalpha=1.0):
    """Display histogram with given number of bins and colour and overplotted gaussian"""

    if isinstance(colour, str):
        colour = string.split(colour, ',')

    freqs, sizes, patches = plt.hist(values, bins=bins, color=colour[0], alpha=histalpha)

    resc = np.sum(freqs * np.diff(sizes))

    mv = values.mean()
    stv = values.std()

    gsv = ss.norm.pdf(sizes, loc=mv, scale=stv) * resc
    plt.plot(sizes, gsv, color=colour[-1], alpha=plotalpha)
