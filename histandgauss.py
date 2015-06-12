# Use plotting library to display histogram and overplat gaussian

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as ss

def histandgauss(values, bins=20, colour='blue'):
    """Display histogram with given number of bins and colour and overplotted gaussian"""

    freqs, sizes, patches = plt.hist(values, bins=bins, color=colour)

    resc = np.sum(freqs * np.diff(sizes))

    mv = values.mean()
    stv = values.std()

    gsv = ss.norm.pdf(sizes, loc=mv, scale=stv) * resc
    plt.plot(sizes, gsv, color=colour)

    