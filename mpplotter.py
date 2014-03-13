# Plot functions using GNUplot

import matplotlib.pyplot as plt
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
        self.width = 15
        self.height = 10

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

        if not self.xrange.notused: plt.xlim(self.xrange.lower, self.xrange.upper)
        if not self.yrange.notused: plt.ylim(self.yrange.lower, self.yrange.upper)

        for rn in self.ranges.listranges():
            r = self.ranges.getrange(rn)
            col = r.rgbcolour()
            if self.xrange.inrange(r.lower):
                print "plotting lower %.6f from %.6f to %.6f\n" % (r.lower, self.yrange.lower, self.yrange.upper)
                plt.axvline(x=r.lower, ymin=self.yrange.lower, ymax=self.yrange.upper, color=col)
            if self.xrange.inrange(r.upper):
                print "plotting upper %.6f from %.6f to %.6f\n" % (r.upper, self.yrange.lower, self.yrange.upper)
                plt.axvline(x=r.upper, ymin=self.yrange.lower, ymax=self.yrange.upper, color=col)
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

