# @Author: John M Collins <jmc>
# @Date:   2018-07-31T15:15:46+01:00
# @Email:  jmc@toad.me.uk
# @Filename: wcscoord.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:52:12+00:00

# Use Simbad and astropy/astroquery to get object name from coords and vice versa

import numpy as np
from astropy import wcs

class wcscoord(object):
    """Class to manage WGC coord lookups"""

    def __init__(self, fitshdr):

        self.wgcstr = wcs.WCS(fitshdr)
        self.offsetpix = np.array((0,0))

    def set_offsets(self, xoffset = None, yoffset = None):
        """Set pixel offsets after triming the front or bottom of array"""
        if xoffset is not None:
            self.offsetpix[0] = xoffset
        if yoffset is not None:
            self.offsetpix[1] = yoffset

    def pix_to_coords(self, pixlist):
        """Invoke conversion of pixels to RA/DEC adjusting for offsets"""
        return self.wgcstr.wcs_pix2world(np.array(pixlist) + self.offsetpix, 0)

    def coords_to_pix(self, coordlist):
        """Convert coords to pixels adjusting offset"""
        return self.wgcstr.wcs_world2pix(coordlist, 0) - self.offsetpix

    def abspix(self, pixlist):
        """Adjust pixels by offsets to give absolute pix coords in original map"""
        return np.array(pixlist) + self.offsetpix

    def relpix(self, pixlist):
        """Get relative pixels from absolute ones"""
        return np.array(pixlist) - self.offsetpix
