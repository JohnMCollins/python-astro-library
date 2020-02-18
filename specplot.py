# Generalised stuff for displaying spectra files

import matplotlib.pyplot as plt
import numpy as np

class SpecplotError(Exception):
    """Throw me if I hit trouble"""
    pass

def getticks(arr, step):
    """Get array argument for xticks or yticks from step given"""
    minx = min(arr)
    maxx = max(arr)
    rl = np.ceil(minx/step) * step
    ru = np.floor(maxx/step) * step
    return np.arange(rl, ru + step, step)

def getoffsets(arr, offs):
    """Get pair of paramaters to set x or y ranges"""
    minx = min(arr)
    maxx = max(arr)
    return  (minx-offs, maxx+offs)

class Specplot(object):

    """General class for getting a plot together"""

    def __init__(self):
        self.wavelengths = None
        self.intensities = None
        self.xtickstep = None
        self.ytickstep = None
        self.xpad = None
        self.ypad = None

    def loadfile(self, fname, wlcol = 0, intencol = 1):
        """Load up a spectrum file, specify

        fname = file name
        wlcol = column giving wavelengths default 0
        intencol = column giving intensities default 1"""

        arr = np.loadtxt(fname)
        arr = np.transpose(arr)
        self.wavelengths = arr[wlcol]
        self.intensities = arr[intencol]

    def setstepoffset(self, xstep = None, ystep = None, xoff = None, yoff = None):
        """Set tick step and offset to pad out display"""
        self.xtickstep = xstep
        self.ytickstep = ystep
        self.xpad = xoff
        self.ypad = yoff
        try:
            self.doplot()
        except SpecplotError:
            pass

    def doplot(self):
        """Actually do the business"""

        if self.wavelengths is None or self.intensities is None:
            raise SpecplotError("No file loaded")

        if self.xtickstep is not None:
            arr = getticks(self.wavelengths, self.xtickstep)
            plt.xticks(arr, arr)

        if self.ytickstep is not None:
            arr = getticks(self.intensities, self.ytickstep)
            plt.yticks(arr, arr)

        if self.xpad is not None:
            plt.xlim(getoffsets(self.wavelengths, self.xpad))

        if self.ypad is not None:
            plt.ylim(getoffsets(self.intensities, self.ypad))

        plt.plot(self.wavelengths, self.intensities)
        plt.show()
