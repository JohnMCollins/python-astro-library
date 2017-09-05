# Limb-darkening laws

import numpy as np
import math

def claret_linear(mu, coeff):
    """Calculate Claret-sytle linear (nb scalar coeff)"""
    return 1.0 - coeff * (1.0 - mu)

def claret_quadratic(mu, coeffs):
    """Calculcate Claret-style quadratic"""
    a, b = coeffs
    return 1.0 - a * (1.0 - mu) - b * (1.0 - mu)**2

def claret_sqrt(mu, coeffs):
    """Calculate Clater-style square root"""
    c, d = coeffs
    return 1.0 - c * (1.0 - mu) - d * (1.0 - math.sqrt(mu))

def claret_log(mu, coeffs):
    """Calculate Claret-style logarithmic"""
    e, f = coeffs
    return 1.0 - e * (1.0 - mu) - f * mu * math.log(mu)

def claret_nonlin(mu, coeffs):
    """Calculate Claret-style non-linear"""
    smu = math.sqrt(mu)
    a1,a2,a3,a4 = coeffs
    return  1.0 - a1 * (1.0 - smu) - a2 * (1.0 - mu) - a3 * (1.0 - mu*smu) - a4 * (1.0 - mu*mu)
