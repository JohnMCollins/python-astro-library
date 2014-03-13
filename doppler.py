# Doppler shift operations

import xyvalue

def doppler(lamobs, vel):
    """Calculate real wavelength from observed wavelength with given velocity"""
    return lamobs / (1.0 + vel/299792.458)

def apply_doppler_array(specarray, vel):
    """Apply doppler shift to the first column of a Python array"""
    return [(doppler(a[0], vel), a[1]) for a in specarray]

def apply_doppler_xy(specarray, vel):
  """Apply doppler shift to the first column of an array of spectral data and return the result"""
  return [xyvalue.XYvalue(doppler(a.xvalue, vel), a.yvalue) for a in specarray]

