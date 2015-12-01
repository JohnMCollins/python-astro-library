# Generate noise and add it to a row of Values

import numpy as np
import numpy.random as nr
import math

def ms(s):
    """Get root mean square of values"""

    return np.mean(np.square(s))

def noise(sig, snr, unorm = 0.0):
    """Add given noise of given s/n ratio to given signal and return result"""
    ls = len(sig)
    nval = nr.uniform(-.5, .5, size = ls) * (1.0 - unorm) + nr.normal(size = ls) * unorm
    return sig + nval * np.sqrt(ms(sig) / (ms(nval) * 10.0 ** (snr / 10.0)))

def getnoise(sig, errs):
    """Calculate SNR from signal and errors"""
    return 10.0 * math.log10(ms(sig)/ms(errs))