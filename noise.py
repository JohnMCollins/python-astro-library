# Generate noise and add it to a row of Values

import numpy as np
import numpy.random as nr

def rms(s):
    """Get root mean square of values"""

    return np.sqrt(np.mean(np.square(s)))

def noise(sig, snr, unorm = 0.0):
    """Add given noise of given s/n ratio to given signal and return result"""
    if snr <= 0.0:
        return sig
    ls = len(sig)
    nval = nr.uniform(-.5, .5, size = ls) * (1.0 - unorm) + nr.normal(size = ls) * unorm
    return sig + nval * rms(sig) / (snr * rms(nval))
