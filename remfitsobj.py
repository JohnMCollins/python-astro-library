# XML Utility functions

# XML routines for object info database

import os
import os.path
import string
import re
import xml.etree.ElementTree as ET
from astropy.time import Time
import datetime
import astropy.units as u
import miscutils
import xmlutil
import numpy as np
import math

SPI_DOC_NAME = "REMOBJ"
SPI_DOC_ROOT = "remobj"

SUFFIX = 'remobj'

class  RemObjError(Exception):
    """Class to report errors"""

    def __init__(self, message, warningonly = False):
        super(RemObjError, self).__init__(message)
        self.warningonly = warningonly

class  Remobj(object):
    """Represent remote object found in file"""

    def __init__(self, name = "", pixcol=0, pixrow=0, ra=0.0, dec=0.0):
        self.objname = name
        self.pixcol = pixcol
        self.pixrow = pixrow
        self.ra = ra
        self.dec = dec
        self.apradius = None
        self.aducount = None
        self.aduerror = None

    def sortorder(self):
        """Rough and ready way to sort list"""
        return self.ra * 1000.0 + self.dec + 90.0

    def load(self, node):
        """Load object details from node"""
        self.objname = ""
        self.pixcol = 0
        self.pixrow = 0
        self.ra = 0.0
        self.dec = 0.0
        self.apradius = None
        self.aducount = None
        self.aduerror = None
        for child in node:
            tagn = child.tag
            if tagn == "name":
                self.objname = xmlutil.gettext(child)
            elif tagn == "pixcol":
                self.pixcol = xmlutil.getint(child)
            elif tagn == "pixrow":
                self.pixrow = xmlutil.getint(child)
            elif tagn == "ra":
                self.ra = xmlutil.getfloat(child)
            elif tagn == "dec":
                self.dec = xmlutil.getfloat(child)
            elif tagn == "aprad":
                self.aprad = xmlutil.getint(child)
            elif tagn == "adu":
                self.aducount = xmlutil.getfloat(child)
            elif tagn == "adue":
                self.aduerror = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save object details to node"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "name", self.objname)
        if self.pixcol != 0:
            xmlutil.savedata(doc, node, "pixcol", self.pixcol)
        if self.pixrow != 0:
            xmlutil.savedata(doc, node, "pixrow", self.pixrow)
        if self.ra != 0.0:
            xmlutil.savedata(doc, node, "ra", self.ra)
        if self.dec != 0.0:
            xmlutil.savedata(doc, node, "dec", self.dec)
        if self.apradius is not None:
            xmlutil.savedata(doc, node, "aprad", self.apradius)
        if self.aducount is not None:
            xmlutil.savedata(doc, node, "adu", self.aducount)
        if self.aduerror is not None:
            xmlutil.savedata(doc, node, "adue", self.aduerror)

class  Remobjlist(object):
    """Represent list of above objects"""

    def __init__(self, filename = "", obsdate = None, filter = None):
        self.filename = filename
        self.obsdate = obsdate
        self.filter = filter
        self.target = None
        self.objlist = []
        self.airmass = None
        self.skylevel = None
        self.percentile = None

    def __hash__(self):
        try:
            return  int(round(self.obsdate * 1e6))
        except TypeError:
            raise RemObjError("Incomplete observation type")

    def set_basedir(self, olddir, newdir):
        """Reset filename to be relative to newdir rather than olddir"""
        if len(self.filename) == 0: return
        tfile = os.path.join(olddir, self.filename)
        self.filename = os.path.relpath(tfile, newdir)

    def addtarget(self, obj):
        """Set target"""
        oldtarget = self.target
        self.target = obj
        if oldtarget is not None:
            raise RemObjError("Target was already set to " + oldtarget.objname, True)

    def addobj(self, obj):
        """Add object to list"""
        self.objlist.append(obj)
        self.objlist.sort(key=lambda x: x.sortorder())

    def load(self, node):
        """load object list from node"""
        self.filename = ""
        self.obsdate = None
        self.filter = None
        self.target = None
        self.objlist = []
        self.airmass = None
        self.skylevel = None
        self.percentile = None
        for child in node:
            tagn = child.tag
            if tagn == "filename":
                self.filename = xmlutil.gettext(child)
            elif tagn == "obsdate":
                self.obsdate = xmlutil.getfloat(child)
            elif tagn == 'filter':
                self.filter = xmlutil.gettext(child)
            elif tagn == "target":
                self.target = Remobj()
                self.target.load(child)
            elif tagn == "refobjs":
                for rchild in child:
                    ro = Remobj()
                    ro.load(rchild)
                    self.objlist.append(ro)
            elif tagn == "airmass":
                self.airmass = xmlutil.getfloat(child)
            elif tagn == "skylevel":
                self.skylevel = xmlutil.getfloat(child)
            elif tagn == "percentile":
                self.percentile = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save object list to node"""
        node = ET.SubElement(pnode, name)
        if len(self.filename) != 0:
            xmlutil.savedata(doc, node, "filename", self.filename)
        if self.obsdate is not None:
            xmlutil.savedata(doc, node, "obsdate", self.obsdate)
        if self.filter is not None:
            xmlutil.savedata(doc, node, "filter", self.filter)
        if self.target is not None:
            self.target.save(doc, node, "target")
        if len(self.objlist) != 0:
            onode = ET.SubElement(node, "refobjs")
            for ob in self.objlist:
                ob.save(doc, onode, "obj")
        if self.airmass is not None:
            xmlutil.savedata(doc, node, "airmass", self.airmass)
        if self.skylevel is not None:
            xmlutil.savedata(doc, node, "skylevel", self.skylevel)
        if self.percentile is not None:
            xmlutil.savedata(doc, node, "percentile", self.percentile)

class  RemobjSet(object):
    """Class to remember a whole set of obs"""

    def __init__(self, targname = None):
        self.filename = None
        self.xmldoc = None
        self.xmlroot = None
        self.basedir = os.getcwd()
        self.targname = targname
        self.obslookup = dict()

    def addobs(self, obs, updateok = False):
        """Add obs results to list. forbid updating unless updateok given"""
        if obs in self.obslookup and not updateok:
            raise RemObjError("Already got obs for date %.6f filter %s" % (obs.obsdate, obs.filter))
        obs.filename = os.path.abspath(obs.filename)
        obs.set_basedir(os.path.dirname(obs.filename), self.basedir)
        self.obslookup[obs] = obs

    def getobslist(self, filter = None, adjfiles = True, firstdate = None, lastdate = None, resultsonly = False):
        """Get a list of observations for processing, in date order.
        If filter specified, restrict to those
        adjust files to be relative to current directory if adjfiles set"""
        oblist = list(self.obslookup.values())
        if resultsonly:
            oblist = [x for x in oblist if x.skylevel is not None]
        if filter is not None:
            oblist = [x for x in oblist if x.filter == filter ]
        if firstdate is not None:
            oblist = [x for x in oblist if x.obsdate >= firstdate ]
        if lastdate is not None:
            oblist = [x for x in oblist if x.obsdate <= lastdate ]
        oblist.sort(key = lambda x: x.obsdate)
        if adjfiles:
            cwd = os.getcwd()
            if cwd != self.basedir:
                for ob in oblist:
                    ob.set_basedir(self.basedir, cwd)
        return oblist

    def set_basedir(self, newdir):
        """Change basdire to new directory"""
        newdir = os.path.abspath(newdir)
        if newdir == self.basedir:
            return
        for ob in self.obslookup:
            ob.set_basedir(self.basedir, newdir)
        self.basedir = newdir

    def loadfile(self, filename):
        """Load up a filename"""
        nlookup = dict()
        filename = miscutils.addsuffix(filename, SUFFIX)
        try:
            self.xmldoc, self.xmlroot = xmlutil.load_file(filename, SPI_DOC_ROOT)
            self.filename = filename
            for c in self.xmlroot:
                tagn = c.tag
                if tagn == "obs":
                    for obc in c:
                        ob = Remobjlist()
                        ob.load(obc)
                        nlookup[ob] = ob
                elif tagn == "target":
                    self.targname = xmlutil.gettext(c)
                elif tagn == "basedir":
                    self.basedir = xmlutil.gettext(c)
        except xmlutil.XMLError as e:
            raise RemObjError(e.args[0], warningonly=e.warningonly)
        self.obslookup = nlookup

    def savefile(self, filename = None):
        """Save stuff to file"""
        outfile = self.filename
        if filename is not None: outfile = miscutils.addsuffix(filename, SUFFIX)
        if outfile is None:
            raise RemObjError("No out file given")
        try:
            self.xmldoc, self.xmlroot = xmlutil.init_save(SPI_DOC_NAME, SPI_DOC_ROOT)
            if len(self.obslookup) != 0:
                c = ET.SubElement(self.xmlroot, 'obs')
                for ob in self.obslookup:
                    ob.save(self.xmldoc, c, "ob")
            if self.targname is not None:
                xmlutil.savedata(self.xmldoc, self.xmlroot, "target", self.targname)
            xmlutil.savedata(self.xmldoc, self.xmlroot, "basedir", self.basedir)
            xmlutil.complete_save(outfile, self.xmldoc)
            self.filename = outfile
        except xmlutil.XMLError as e:
            raise RemObjError("Save file XML error - " + e.args[0])
