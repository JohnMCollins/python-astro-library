"""Run coordinate converssion program takeing care of offsets"""

# @Author: John M Collins <jmc>
# @Date:   2018-07-31T15:15:46+01:00
# @Email:  jmc@toad.me.uk
# @Filename: wcscoord.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:52:12+00:00

# import sys
import numpy as np
from astropy import wcs


class wcscoord:
    """Class to manage WGC coord lookups

    For the avoidance of doubt:

    Offsets give where WCS expects them to be minus where they are in the array."""

    def __init__(self, fitshdr):

        self.wgcstr = wcs.WCS(fitshdr)
        self.offsetpix = np.array((0, 0))

    def set_offsets(self, xoffset=None, yoffset=None):
        """Set pixel offsets after triming the front or bottom of array"""
        self.offsetpix[0] = xoffset
        self.offsetpix[1] = yoffset

    def accum_offsets(self, xoffset=None, yoffset=None):
        """Accumulate offsets after noting offset in FITS array"""
        try:
            self.offsetpix[0] += xoffset
            self.offsetpix[1] += yoffset
        except TypeError:
            self.set_offsets(xoffset, yoffset)

    def pix_to_coords(self, pixlist):
        """Invoke conversion of pixels to RA/DEC adjusting for offsets"""
#         if np.count_nonzero(self.offsetpix) != 0:
#             print("Inserting offset", self.offsetpix[0], self.offsetpix[1], file=sys.stderr)
        return self.wgcstr.wcs_pix2world(np.array(pixlist) + self.offsetpix, 0)

    def coords_to_pix(self, coordlist):
        """Convert coords to pixels adjusting offset"""
#         if np.count_nonzero(self.offsetpix) != 0:
#             print("Subtracting offset", self.offsetpix[0], self.offsetpix[1], file=sys.stderr)
        return self.wgcstr.wcs_world2pix(coordlist, 0) - self.offsetpix

    def abspix(self, pixlist):
        """Adjust pixels by offsets to give absolute pix coords in original map"""
        return np.array(pixlist) + self.offsetpix

    def relpix(self, pixlist):
        """Get relative pixels from absolute ones"""
        return np.array(pixlist) - self.offsetpix

    def colrow_to_coords(self, col, row):
        """Do one-off conversion of column and row to coords"""
        return  self.pix_to_coords(((col, row),))[0]

    def coords_to_colrow(self, ra, dec):
        """Return pixel col/row corresponding to coords"""
        return  self.coords_to_pix(((ra, dec),))[0]
