# Doppler shift operations

import xyvalue
import numpy as np

def doppler(lamobs, vel):
    """Calculate real wavelength from observed wavelength with given velocity"""
    return lamobs / (1.0 + vel/299792.458)

def rev_doppler(lamreal, vel):
    """Calculate observable wl from real wl with given velocity"""
    return lamreal / (1.0 - vel/299792.458)

vec_doppler = np.vectorize(doppler)
vec_rev_doppler = np.vectorize(rev_doppler)

def apply_doppler_array(specarray, vel):
    """Apply doppler shift to the first column of a Python array"""
    return [(doppler(a[0], vel), a[1]) for a in specarray]

def apply_doppler_xy(specarray, vel):
  """Apply doppler shift to the first column of an array of spectral data and return the result"""
  return [xyvalue.XYvalue(doppler(a.xvalue, vel), a.yvalue) for a in specarray]

