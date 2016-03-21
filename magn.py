# Generate noise and add it to a row of Values

import numpy as np

def fluxtomag(inten):
    """Convert intensity to magnitude""" 
    return -2.5 * np.log10(inten)

def magtoflux(mag):
    """Convert magnitude to flux"""
    return 10.0 ** (mag / -2.5)
 