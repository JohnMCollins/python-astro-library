# Plot functions using GNUplot

import Gnuplot
import string
import copy

import datarange
import xmlutil

class Plotter_error(Exception):
    """Throw this class if something goes wrong with the plot"""
    pass

class Plotter_options(object):
    """Options to remember options for plotting with"""

    def __init__(self):
        self.width = 600
        self.height = 400

    def setdims(self, width = None, height = None):
        """Set dimensions as required"""
        if width is not None: self.width = width
        if height is not None: self.height = height

    def load(self, node):
        """Load settings from XML file"""
        child = node.firstChild()
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "width":
                self.width = xmlutil.getint(child)
            elif tagn == "height":
                self.height = xmlutil.getint(child)
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save settings to XML file"""
        node = doc.createElement(name)
        pnode.appendChild(node)
        xmlutil.savedata(doc, node, "width", self.width)
        xmlutil.savedata(doc, node, "height", self.height)

class Plotter(object):
    """Class to run GNUplot"""

    def __init__(self, opts):
        self.gp = Gnuplot.Gnuplot()
        self.gp("set term x11 size %d,%d" % (opts.width, opts.height))
        self.xrange = None
        self.yrange = None
        self.ranges = []
        self.title = None
        self.active = False
        self.resetreq = False
        self.ranges = datarange.RangeList()

    def reset(self):
        """Reset stuff before plotting again"""
        self.resetreq = True
        self.ranges.clear()

    def clear(self):
        """Clear plot usually on error"""
        self.gp("clear")

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

    def set_plot(self, plotfiles = []):
        """Create plot from list of plot files"""
        if len(plotfiles) == 0:
            if self.active: self.gp("clear")
            return
        if self.xrange is None or self.yrange is None:
            raise Plotter_error("X and Y ranges not set")

        if self.active:
            if self.resetreq:
                self.gp("reset")
                self.gp("unset arrow")

        if not self.xrange.notused: self.gp("set xrange [%.3f:%.3f]" % (self.xrange.lower, self.xrange.upper))
        if not self.yrange.notused: self.gp("set yrange [%.1f:%.1f]" % (self.yrange.lower, self.yrange.upper))

        for rn in self.ranges.listranges():
            r = self.ranges.getrange(rn)
            col = r.rgbcolour()
            if self.xrange.inrange(r.lower):
                self.gp("set arrow from %.3f,%.1f to %.3f,%.1f lc rgbcolor '%s' nohead" % (r.lower, self.yrange.lower, r.lower, self.yrange.upper, col))
            if self.xrange.inrange(r.upper):
                self.gp("set arrow from %.3f,%.1f to %.3f,%.1f lc rgbcolor '%s' nohead" % (r.upper, self.yrange.lower, r.upper, self.yrange.upper, col))

        plotcmds = [ "'%s' w l notitle" % p for p in plotfiles]
        self.gp("plot " + string.join(plotcmds, ','))
        self.active = True
        self.resetreq = False

class Resultplot:
    """Run GNUplot to display results file"""

    def __init__(self, opts):
        self.gp = Gnuplot.Gnuplot()
        self.gp("set term x11 size %d,%d" % (opts.width, opts.height))

    def display(self, filelist):
        """Display results filelist assumed in format (filename, starting_time)"""

        plotcmds = [ "'%s' w l title '%g'" % x for x in filelist ]
        self.gp("plot " + string.join(plotcmds, ','))

