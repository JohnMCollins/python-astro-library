# Plot functions using GNUplot

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mptch
import string
import copy
import xml.etree.ElementTree as ET

import datarange
import xmlutil

# Record of current widths and heights we are using

Cwidth = 15.0
Cheight = 10.0

class Plotter_error(Exception):
    """Throw this class if something goes wrong with the plot"""
    pass

def Setdims(width = None, height = None):
    """Set dimensions of Window"""
    global Cwidth, Cheight
    if width is not None: Cwidth = width
    if height is not None: Cheight = height
    plt.rcParams['figure.figsize'] = (Cwidth, Cheight)

class Plotter(object):
    """Class to run matplotlib"""

    def __init__(self):
        self.xrange = None
        self.yrange = None
        self.ranges = datarange.RangeList()
        self.oldversion = matplotlib.__version__ == '1.0.0'

    def set_xrange(self, xr):
        """Set X display range"""
        try:
            self.xrange = xr.checkvalid()
        except datarange.DataRangeError as e:
            raise Plotter_error(e.args[0])

    def set_yrange(self, yr):
        """Set Y display range"""
        try:
            self.yrange = yr.checkvalid()
        except datarange.DataRangeError as e:
            raise Plotter_error(e.args[0])

    def set_subrange(self, r):
        """Set a sub range"""
        try:
            self.ranges.setrange(r)
        except datarange.DataRangeError as e:
            raise Plotter_error(e.args[0])

    def set_plot(self, plotarray = [], clist = None, leglist = None):
        """Create plot from list of plot files"""
        if len(plotarray) == 0:  return
        if self.xrange is None or self.yrange is None:
            raise Plotter_error("X and Y ranges not set")
        plt.clf()
        ax = plt.gca()
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.set_xlabel(r'Wavelength $ (\AA)$')
        ax.set_ylabel('Intensity')

        if self.xrange.notused:
            col = self.xrange.rgbcolour()
            plt.axvline(x=self.xrange.lower, color=col, ls="--")
            plt.axvline(x=self.xrange.upper, color=col, ls="--")
        else:
            plt.xlim(self.xrange.lower, self.xrange.upper)
        if self.yrange.notused:
            col = self.yrange.rgbcolour()
            plt.axhline(y=self.yrange.lower, color=col, ls="--")
            plt.axhline(y=self.yrange.upper, color=col, ls="--")
        else:
            plt.ylim(self.yrange.lower, self.yrange.upper)

        yl, yu = ax.get_ylim()
        dr = False
        for rn in self.ranges.listranges():
            r = self.ranges.getrange(rn)
            col = r.rgbcolour()
            ls = "-"
            if r.notused: ls = ":"
            if r.alpha != 0.0:
                ax.add_patch(mptch.Rectangle((r.lower, yl), r.upper-r.lower, yu-yl, color=col, alpha=r.alpha))
                dr = True
            else:
                try:
                    plt.axvline(x=r.lower, color=col, ls=ls)
                except ValueError:
                    pass
                try:
                    plt.axvline(x=r.upper, color=col, ls=ls)
                except ValueError:
                    pass
        if dr:
            plt.gcf().canvas.draw()

        linelist = []
        if clist is not None:
            for c,p in zip(clist,plotarray):
                line, = plt.plot(p.get_xvalues(), p.get_yvalues(), color=c)
                linelist.append(line)
        else:
            for p in plotarray:
                line, = plt.plot(p.get_xvalues(), p.get_yvalues())
                linelist.append(line)
        if leglist is not None:
            plt.legend(linelist, leglist)
        plt.show()

    def close(self):
        plt.close()

    def savefig(self, pltfile):
        """Save current figure to file name given"""
        plt.gcf().savefig(pltfile)
