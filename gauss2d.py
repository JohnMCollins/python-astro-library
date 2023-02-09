"""Two-dimensional Gaussians"""

import numpy as np

def gauss2d(xpts, ypts, amp, sigma):
    """Compute gaussian from similar-shapped x and y"""
    return  amp * np.exp((xpts**2 + ypts**2) / (-2.0 * sigma ** 2))

def gauss_circle(pts, xoffset, yoffset, amp, sigma):
    """Compute 2D gaussian with given amplitude and sigma
    pts is a tuple of x and y points"""
    return gauss2d(pts[:,1] - xoffset, pts[:,0] - yoffset, amp, sigma)

def gauss_with_error(pts, xoffset, yoffset, amp, sigma, ampsig, sigmasig):
    """Compute 2D gaussian with error term"""
    xpts = pts[:,1] - xoffset
    ypts = pts[:,0] - yoffset
    G = gauss2d(xpts, ypts, amp, sigma)
    VG = G**2 * ((ampsig/amp)**2 + sigmasig**2 * (xpts**2 + ypts**2)**2/sigma**6)
    return  (G, np.sqrt(VG))

def lorentz_circle(pts, xoffset, yoffset, gamma):
    """Compute 2D lorentz with given gamma
    pts is a tuple of x and y points"""
    xpt = pts[:,1] - xoffset
    ypt = pts[:,0] - yoffset
    return  (0.5 / np.pi) * gamma / (xpt**2 + ypt**2 + gamma**2)**1.5
