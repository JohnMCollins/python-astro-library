# Class for holding spectral data values

import xmlutil
import datarange
from functools import reduce

class Specdatum:
    """This class is used to hold spectral data points with given uncertainty

Possibly we'll do it another way later."""

    def __init__(self, xval = 0.0, yval = 0.0, yerr = 0.0):
        self.xvalue = float(xval)
        self.yvalue = float(yval)
        self.yerror = float(yerr)

    def load(self, node):
        """Load from XML file"""
        child = node.firstChild()
        self.yerror = 0.0
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "xvalue":
                self.xvalue = xmlutil.getfloat(child)
            elif tagn == "yvalue":
                self.yvalue = xmlutil.getfloat(child)
            elif tagn == "yerr":
                self.yerror = xmlutil.getfloat(child)
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save to XML file"""
        node = doc.createElement(name)
        xmlutil.savedata(doc, node, "xvalue", self.xvalue)
        xmlutil.savedata(doc, node, "yvalue", self.yvalue)
        if self.yerror != 0.0: xmlutil.savedata(doc, node, "yerr", self.yerror)
        pnode.appendChild(node)

class Specarray(object):
    """This class is used to hold a list of spectral data.

    We hold the Modified Julian Date and the Barycentric date"""

    def __init__(self, modjdate = 0.0, baryjdate = 0.0, radialvel = 0.0, filename = ""):
        self.modjdate = modjdate
        self.baryjdate = baryjdate
        self.radialvel = radialvel
        self.datalist = []
        self.filename = filename

    def copy_in(self, specarray, xcol = 0, ycol = 1, eycol = -1):
        """Copy data from the spectrum matrix.

        xcol gives the column for the X values (default 0)
        ycol gives the column for the Y values (default 1)
        eycol gives the column for the y uncertainty (default -1 meaning none)"""

        if eycol >= 0:
            self.datalist = [Specdatum(a[xcol], a[ycol], a[eycol]) for a in specarray]
        else:
            self.datalist = [Specdatum(a[xcol], a[ycol]) for a in specarray]

    def __getitem__(self, n):
        return self.datalist[n]

    def getmaxmin(self):
        """Get pair of upper and lower ranges of data"""
        xvalues = [item.xvalue for item in self.datalist]
        yvalues = [item.yvalue for item in self.datalist]
        return (datarange.DataRange(lbound=min(*xvalues),ubound=max(*xvalues),descr='X range'),datarange.DataRange(lbound=min(*yvalues),ubound=max(*yvalues),descr='Y range'))

    def append(self, spectdata):
        """Append spectrum data to list"""
        self.datalist.append(spectdata)

    def get_matrix(self):
        """Return a matrix of xvalues, yvalues, errors"""
        return [(a.xvalue, a.yvalue, a.yerror) for a in self.datalist]

    def write_datafile(self, filename):
        """Write a file as a set of X,Y columns"""
        fout = None
        try:
            fout = open(filename, "w")
            for item in self.datalist:
                fout.write("%.6f %.6f\n" % (item.xvalue, item.yvalue))
            fout.close()
        except IOError:
            pass
        finally:
            if fout is not None:
                fout.close()

    def load(self, node):
        """Load from XML file"""
        child = node.firstChild()
        self.filename = ""
        self.radialvel = 0.0
        self.datalist = []
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "modjdate":
                self.modjdate = xmlutil.getfloat(child)
            elif tagn == "baryjdate":
                self.baryjdate = xmlutil.getfloat(child)
            elif tagn == "filename":
                self.filename = xmlutil.gettext(child)
            elif tagn == "radialvel":
                self.radialvel = xmlutil.getfloat(child)
            elif tagn == "dlist":
                listc = child.firstChild()
                while not listc.isNull():
                    if listc.toElement().tagName() == "datum":
                        dat = Specdatum()
                        dat.load(listc)
                        self.datalist.append(dat)
                    listc = listc.nextSibling()
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save to XML file"""
        node = doc.createElement(name)
        xmlutil.savedata(doc, node, "modjdate", self.modjdate)
        xmlutil.savedata(doc, node, "baryjdate", self.baryjdate)
        if len(self.filename) != 0: xmlutil.savedata(doc, node, "filename", self.filename)
        if self.radialvel != 0.0: xmlutil.savedata(doc, node, "radialvel", self.radialvel)
        pnode.appendChild(node)
        if len(self.datalist) != 0:
            dnode = doc.createElement("dlist")
            node.appendChild(dnode)
            for item in self.datalist:
                item.save(doc, dnode, "datum")

class Specarraylist(object):
    """Make ourselves a list of such creatures"""

    def __init__(self):
        self.obs_list = []
        self.yscale = 1.0

    def __getitem__(self, n):
        return self.obs_list[n]

    def append(self, item):
        """Append a Specarray (assumed) to list"""
        self.obs_list.append(item)

    def obslist(self):
        """Return the observation list as an iterator"""
        for indx in self.obs_list:
            yield indx

    def set_obslist(self, olist):
        """Reset the observation list"""
        self.obs_list = olist

    def __getitem__(self, n):
        return self.obs_list[n]

    def getmaxmin(self):
        """Get maximum xy as a pair of ranges"""
        maxmins = [item.getmaxmin() for item in self.obslist()]
        return (reduce(datarange.MergeRange,[p[0] for p in maxmins]), reduce(datarange.MergeRange,[p[1] for p in maxmins]))

    def load(self, node):
        """Load from XML file"""
        child = node.firstChild()
        self.yscale = 1.0
        self.obs_list = []
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "obslist":
                listc = child.firstChild()
                while not listc.isNull():
                    if listc.toElement().tagName() == "observation":
                        dat = Specarray()
                        dat.load(listc)
                        self.obs_list.append(dat)
                    listc = listc.nextSibling()
            child = child.nextSibling()

    def save(self, doc, pnode, name):
        """Save to XML file"""
        node = doc.createElement(name)
        xmlutil.savedata(doc, node, "yscale", self.yscale)
        pnode.appendChild(node)
        if len(self.obs_list) != 0:
            dnode = doc.createElement("obslist")
            node.appendChild(dnode)
            for item in self.obs_list:
                item.save(doc, dnode, "observation")



