# Plot functions using GNUplot

import matplotlib.pyplot as plt
import string
import copy
import xml.etree.ElementTree as ET

import datarange
import xmlutil

class Plotter_error(Exception):
    """Throw this class if something goes wrong with the plot"""
    pass

class Plotter_options(object):
    """Options to remember options for plotting with"""

    def __init__(self):
        self.width = 15
        self.height = 10

    def setdims(self, width = None, height = None):
        """Set dimensions as required"""
        if width is not None: self.width = width
        if height is not None: self.height = height

    def load(self, node):
        """Load settings from XML file"""
        for child in node:
            tagn = child.tag
            if tagn == "width":
                self.width = xmlutil.getint(child)
            elif tagn == "height":
                self.height = xmlutil.getint(child)

    def save(self, doc, pnode, name):
        """Save settings to XML file"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "width", self.width)
        xmlutil.savedata(doc, node, "height", self.height)

class Plotter(object):
    """Class to run matplotlib"""

    def __init__(self, opts):
        plt.rcParams['figure.figsize'] = (opts.width, opts.height)
        self.xrange = None
        self.yrange = None
        self.ranges = datarange.RangeList()

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

    def set_plot(self, plotarray = []):
        """Create plot from list of plot files"""
        if len(plotarray) == 0:  return
        if self.xrange is None or self.yrange is None:
            raise Plotter_error("X and Y ranges not set")
        plt.clf()

        if self.xrange.notused:
            col = self.xrange.rgbcolour()
            plt.axvline(x=self.xrange.lower, color=col)
            plt.axvline(x=self.xrange.upper, color=col)    
        else:
            plt.xlim(self.xrange.lower, self.xrange.upper)
        if not self.yrange.notused:
            plt.ylim(self.yrange.lower, self.yrange.upper)

        for rn in self.ranges.listranges():
            r = self.ranges.getrange(rn)
            col = r.rgbcolour()
            try:
                plt.axvline(x=r.lower, color=col)
            except ValueError:
                #print "Value Error lower =", r.lower
                pass
            try:
                plt.axvline(x=r.upper, color=col)
            except ValueError:
                #print "Value Error upper =", r.upper
                pass

        for p in plotarray:
            plt.plot(p.get_xvalues(), p.get_yvalues())
        plt.show()

    def close(self):
        plt.close()

#class Resultplot:
#    """Run GNUplot to display results file"""

#    def __init__(self, opts):
#        self.gp = Gnuplot.Gnuplot()
#        self.gp("set term x11 size %d,%d" % (opts.width, opts.height))

#    def display(self, filelist):
#        """Display results filelist assumed in format (filename, starting_time)"""

#        plotcmds = [ "'%s' w l title '%g'" % x for x in filelist ]
#        self.gp("plot " + string.join(plotcmds, ','))

