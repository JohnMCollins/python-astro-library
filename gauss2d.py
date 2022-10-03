"""Two-dimensional Gaussians"""

import math
import numpy as np


def gauss_circle(pts, amp, sigma):
    """Compute 2D gaussian with given amplitude and sigma
    pts is a tuple of similarly-sized x and y points"""
    xpts, ypts = pts
    return  amp * np.exp((xpts ** 2 + ypts ** 2) / (-2.0 * sigma ** 2))


def gauss_ellipse(pts, amp, sigma_x, sigma_y, theta):
    """Elliptical version with given x and y sigmas and theta to X asis"""
    xpts, ypts = pts
    cos2_theta = math.cos(theta) ** 2
    sin2_theta = math.sin(theta) ** 2
    sigxsq = sigma_x ** 2
    sigysq = sigma_y ** 2

    return  amp * np.exp(-0.5 * ((cos2_theta / sigxsq + sin2_theta / sigysq) * xpts ** 2 +
                                 math.sin(2 * theta) * (1.0 / sigxsq + 1.0 / sigysq) * xpts * ypts +
                                 (sin2_theta / sigxsq + cos2_theta / sigysq) * ypts ** 2))
