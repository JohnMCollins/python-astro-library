# Limb-darkening laws

import numpy as np
import math

def claret_nonlin(mu, coeffs):
    """Calculate Claret-style non-linear"""
    smu = math.sqrt(mu)
    a1,a2,a3,a4 = coeffs
    return  1.0 - a1 * (1.0 - smu) - a2 * (1.0 - mu) - a3 * (1.0 - mu*smu) - a4 * (1.0 - mu*mu)
