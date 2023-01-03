"""Two-dimensional Gaussians"""

import numpy as np

def gauss2d(xpts, ypts, amp, sigma):
    """Compute gaussian from similar-shapped x and y"""
    return  amp * np.exp((xpts**2 + ypts**2) / (-2.0 * sigma ** 2))

def gauss_circle(pts, xoffset, yoffset, amp, sigma):
    """Compute 2D gaussian with given amplitude and sigma
    pts is a tuple of x and y points"""
    return gauss2d(pts[:,1] - xoffset, pts[:,0] - yoffset, amp, sigma)

def lorentz_circle(pts, xoffset, yoffset, gamma):
    """Compute 2D lorentz with given gamma
    pts is a tuple of x and y points"""
    xpt = pts[:,1] - xoffset
    ypt = pts[:,0] - yoffset
    return  (0.5 / np.pi) * gamma / (xpt**2 + ypt**2 + gamma**2)**1.5 