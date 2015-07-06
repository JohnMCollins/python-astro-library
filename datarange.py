# Class type for ranges

import xml.etree.ElementTree as ET
import xmlutil
import copy
import string
import numpy as np

class  DataRangeError(Exception):
    """Class to report errors concerning ranges"""
    pass

class  DataRange(object):
    """Class for data ranges, including save options"""

    def __init__(self, lbound = 0.0, ubound = 100.0, descr = "", shortname = "", red = 0, green = 0, blue = 0, notused = False):
        self.lower = lbound
        self.upper = ubound
        self.description = descr
        self.shortname = shortname
        self.notused = notused
        try:
            self.red = red & 0xff
            self.green = green & 0xff
            self.blue = blue & 0xff
        except TypeError:
            self.red = self.green = self.blue = 0

    def referable(self):
        """Report if the range can be referred to by the short name.

        Currently only if it has one"""
        return len(self.shortname) != 0

    def checkvalid(self):
        """Check range is valid only"""
        if  self.lower < self.upper: return self
        msg = "Invalid range (lower should be less than upper)"
        if self.referable:
            msg = "Range - '" + self.shortname + "' is not valid"
        raise DataRangeError(msg)

    def inrange(self, value):
        """Report if value is in given range"""
        return  value >= self.lower and value <= self.upper

    def setcolour(self, red, green, blue):
        """Set colours as specified"""
        try:
            self.red = red & 0xff
            self.green = green & 0xff
            self.blue = blue & 0xff
        except TypeError:
            self.red = self.green = self.blue = 0

    def rgbcolourvalue(self):
        """Return colour as actual value"""
        return  (self.red << 16) | (self.green << 8) | self.blue

    def setrgbcolour(self, value = 0):
        """Set colours to rgb value"""
        try:
            self.red = (value >> 16) & 0xff
            self.green = (value >> 8) & 0xff
            self.blue = value & 0xff
        except TypeError:
            self.red = self.green = self.blue = 0

    def rgbcolour(self):
        """Return colour as an RGB constant"""
        return "#%.2x%.2x%.2x" % (self.red, self.green, self.blue)

    def select(self, xvalues, *yvalues):
        """Where xvalues and yvalues are numpy arrays of similar shape,

        select the xvalues from the range and the corresponding yvalues
        and return the tuple (xvalues, yvalues)"""

        sel = (xvalues >= self.lower) & (xvalues <= self.upper)
        selres = [ xvalues[sel] ]
        for yv in yvalues:
            selres.append(yv[sel])
        return selres

    def selectnot(self, xvalues, *yvalues):
        """Where xvalues and yvalues are numpy arrays of similar shape,

        select the xvalues not from the range and the corresponding yvalues
        and return the tuple"""

        sel = (xvalues < self.lower) | (xvalues > self.upper)
        selres = [ xvalues[sel]]
        for yv in yvalues:
            selres.append(yv[sel])
        return selres

    def argselect(self, xvalues):
        """Return the indices of the ends of the range delineated by the selection"""

        wh = np.where((xvalues >= self.lower) & (xvalues <= self.upper))[0]
        if len(wh) == 0:
            raise DataRangeError("No values in range")
        return (wh[0], wh[-1])

    def load(self, node):
        """Load range from XML file"""
        self.description = ""
        self.red = self.green = self.blue = 0
        self.notused = False
        for child in node:
            tagn = child.tag
            if tagn == "lower":
                self.lower = xmlutil.getfloat(child)
            elif tagn == "upper":
                self.upper = xmlutil.getfloat(child)
            elif tagn == "descr":
                self.description = xmlutil.gettext(child)
            elif tagn == "shortn":
                self.shortname = xmlutil.gettext(child)
            elif tagn == "red":
                self.red = xmlutil.getint(child)
            elif tagn == "green":
                self.green = xmlutil.getint(child)
            elif tagn == "blue":
                self.blue = xmlutil.getint(child)
            elif tagn == "notused":
                self.notused = True

    def save(self, doc, pnode, name):
        """Save range to XML file"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "lower", self.lower)
        xmlutil.savedata(doc, node, "upper", self.upper)
        if len(self.description) != 0:
            xmlutil.savedata(doc, node, "descr", self.description)
        if len(self.shortname) != 0:
            xmlutil.savedata(doc, node, "shortn", self.shortname)
        if self.red != 0: xmlutil.savedata(doc, node, "red", self.red)
        if self.green != 0: xmlutil.savedata(doc, node, "green", self.green)
        if self.blue != 0: xmlutil.savedata(doc, node, "blue", self.blue)
        xmlutil.savebool(doc, node, "notused", self.notused)

def MergeRange(a, b):
    """Merge a pair of ranges into one range with the maximum of the two"""
    res = copy.copy(a)
    res.lower = min(a.lower,b.lower)
    res.upper = max(a.upper,b.upper)
    return res

class RangeList(object):
    """Class for remembering a list of ranges"""

    def __init__(self):
        self.rlist = dict()

    def setrange(self, item):
        """Add range to list of ranges.

        Replaces any existing range of the same short name.
        Error if range doesn't have a short name."""

        if not item.referable():
            raise DataRangeError("No short name for range")

        self.rlist[item.shortname] = item.checkvalid()

    def removerange(self, item):
        """Remove range from list of ranges"""
        try:
            del self.rlist[item.shortname]
        except KeyError:
            raise DataRangeError("Range '" + item.shortname + "' did not exist")

    def getrange(self, sn):
        """Get range for given short name"""
        try:
            return self.rlist[sn]
        except KeyError:
            raise DataRangeError("Range '" + sn + "' does not exist")

    def clear(self):
        """Forget the list of ranges"""
        self.rlist = dict()

    def listranges(self):
        """Return the range names

        NB This isn't sorted"""
        return self.rlist.keys()

    def load(self, node):
        """Load ranges from XML file"""
        for child in node:
            if child.tag == "rng":
                newrg = DataRange()
                newrg.load(child)
                self.setrange(newrg)

    def save(self, doc, pnode, name):
        """Save ranges to XML file"""
        node = ET.SubElement(pnode, name)
        for n in self.rlist.values():
            n.save(doc, node, "rng")

def load_ranges(filename):
    """Load a list of ranges from the given file"""
    try:
        doc, root = xmlutil.load_file(filename)
        ret = RangeList()
        rl = xmlutil.find_child(root, "rangelist")
        ret.load(rl)
        return ret
    except xmlutil.XMLError as e:
        raise DataRangeError("Saved range error - " + e.args[0])

def save_ranges(filename, ranges):
    """Save a list of ranges to the given file"""
    try:
        doc, root = xmlutil.init_save("RANGES", "ranges")
        ranges.save(doc, root, "rangelist")
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise DataRangeError("Saved range error - " + e.args[0])

def init_default_ranges(peakshort = 'halpha', peakdescr = 'H Alpha peak', peakwl = 6562.8, peakwid = 2.0, xwid = 20.0):
    """Create default range set"""

    ret = RangeList()
    ret.setrange(DataRange(lbound = peakwl - xwid/2.0, ubound = peakwl + xwid/2.0, descr = "X axis display range", shortname = "xrange", notused=True))
    ret.setrange(DataRange(lbound = 0.0, ubound = 3.0, descr = "Y axis display range", shortname = "yrange", notused=True))
    #ret.setrange(DataRange(lbound = 6560.3, ubound = 6561.6, descr = "Continuum blue", shortname = "contblue", blue=128))
    #ret.setrange(DataRange(lbound = 6565.4, ubound = 6620.5, descr = "Continuum red", shortname = "contred", red=128))
    ret.setrange(DataRange(lbound = peakwl - peakwid/2.0, ubound = peakwl + peakwid/2.0, descr = peakdescr, shortname = peakshort, red=255))
    #ret.setrange(DataRange(lbound = 6561.46, ubound = 6561.7, descr = "Integration section 1", shortname = "integ1", green=200, blue=200))
    #ret.setrange(DataRange(lbound = 6562.06, ubound = 6562.3, descr = "Integration section 2", shortname = "integ2", red=200, green=200))
    return ret

class Rangeset(object):
    """Set of reanges for when we want to extract points inside all of several or none of several"""

    def __init__(self, lst):
        self.rangeset = dict()
        self.rangelist = lst

    def parseset(self, arg):
        """Parse list of range names and add to set"""

        if arg is None or len(arg) == 0:
            return
        argparts = string.split(arg, ',')
        d = copy.copy(self.rangeset)
        for a in argparts:
            r = self.rangelist.getrange(a)
            d[a] = r
        self.rangeset = d

    def exclude(self, xvalues, *yvalues):
        """Exclude from pairs of xvalues and yvalues the xvalues in any of the ranges given"""

        for r in self.rangeset.values():
            yvalues = r.selectnot(xvalues, *yvalues)
            xvalues = yvalues.pop(0)
        selres = [ xvalues ]
        for yv in yvalues: selres.append(yv)
        return tuple(selres)

    def include(self, xvalues, *yvalues):
        """Include everything that's in any of the ranges"""

        rs = np.zeros_like(xvalues, dtype=np.bool)
        for r in self.rangeset.values():
            rs |= (xvalues >= r.lower) & (xvalues <= r.upper)
        selres = [ xvalues[rs] ]
        for yv in yvalues:
            selres.append(yv[rs])
        return tuple(selres)
