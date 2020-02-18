# Generate noise and add it to a row of Values

import numpy as np
import numpy.random as nr
import math

def ms(s):
    """Get mean square of values"""
    return np.mean(np.square(s))

def rms(s):
    """Get root mean square of values"""
    return math.sqrt(np.mean(np.square(s)))

def noise(sig, snr, unorm = 0.0):
    """Add given noise of given s/n ratio to given signal and return result"""
    ls = len(sig)
    nval = nr.uniform(-.5, .5, size = ls) * (1.0 - unorm) + nr.normal(size = ls) * unorm
    return sig + nval * np.sqrt(ms(sig) / (ms(nval) * 10.0 ** (snr / 10.0)))

def rmsnoise(sig, snr, unorm = 0.0):
    """Add given rms noise to given signal and return result"""
    ls = len(sig)
    nval = nr.uniform(-.5, .5, size = ls) * (1.0 - unorm) + nr.normal(size = ls) * unorm
    return sig + nval * (rms(sig) / rms(nval)) / snr

def getnoise(sig, errs):
    """Calculate SNR from signal and errors"""
    return 10.0 * math.log10(ms(sig)/ms(errs))

def getrmsnoise(sig, errs):
    """Calculate RMS verions of SNR"""
    return rms(sig)/rms(errs)

def rms2db(rms):
    """Convert rms SNR to dB copes with numpy vectors"""
    return 20.0 * np.log10(rms)     # Times 2 to cancel sqrt and times 10 to dB

def db2rms(db):
    """Convert dB SNR to RMS coes with numpy vectors"""
    try:
        return 10.0 ** (db / 20.0)
    except TypeError:
        return 10.0 ** (np.array(db) / 20.0)
