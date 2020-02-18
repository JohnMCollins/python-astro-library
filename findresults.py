# Record of find results

import os
import sys
import string
import xml.etree.ElementTree as ET
import xmlutil

class FindResError(Exception):
    """Throw in case of errors"""
    pass

class FindRes(object):
    """Remember number of pixels to trim from each end of each frame"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Initialise fields"""

        self.name = None
        self.pixrow = None
        self.pixcol = None
        self.ra = None
        self.dec = None
        self.apsize = None
        self.aducount = None

    def load(self, node):
        """Load fields from XML file"""

        self.reset()

        for child in node:
            tagn = child.tag
            if tagn == "name":
                self.name = xmlutil.gettext(child)
            elif tagn == "pixrow":
                self.pixrow = xmlutil.getint(child)
            elif tagn == "pixcol":
                self.pixcol = xmlutil.getint(child)
            elif tagn == "ra":
                self.ra = xmlutil.getfloat(child)
            elif tagn == "dec":
                self.dec = xmlutil.getfloat(child)
            elif tagn == "apsize":
                self.apsize = xmlutil.getint(child)
            elif tagn == "aducount":
                self.aducount = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.name is not None:
            xmlutil.savedata(doc, node, "name", self.name)
        if self.pixrow is not None:
            xmlutil.savedata(doc, node, "pixrow", self.pixrow)
        if self.pixcol is not None:
            xmlutil.savedata(doc, node, "pixcol", self.pixcol)
        if self.ra is not None:
            xmlutil.savedata(doc, node, "ra", self.ra)
        if self.dec is not None:
            xmlutil.savedata(doc, node, "dec", self.dec)
        if self.apsize is not None:
            xmlutil.savedata(doc, node, "apsize", self.apsize)
        if self.aducount is not None:
            xmlutil.savedata(doc, node, "aducount", self.aducount)

class FindResSet(object):
    """Represent common parameters for Rem programs"""

    def __init__(self, filename = None, obsind = None, fitsind = None):
        self.filename = filename
        self.obsind = obsind
        self.fitsind = fitsind
        self.findlist = []

    def add_result(self, res):
        """Add a result to list"""
        self.findlist.append(res)

    def del_result(self, res):
        """Remove a result"""
        self.findlist = [l for l in self.findlist if l is not res]

    def number_results(self):
        """return number of result"""
        return len(self.findlist)

    def get_list(self):
        """Generator to loop over find results"""
        for l in self.findlist:
            yield l

    def load(self, node):
        """Load results from XML file"""

        self.filename = None
        self.obsind = None
        self.fitsind = None
        self.findlist = []

        for child in node:
            tagn = child.tag
            if tagn == "filename":
                self.filename = xmlutil.gettext(child)
            elif tagn == "obsind":
                self.obsind = xmlutil.getint(child)
            elif tagn == "fitsind":
                self.fitsind = xmlutil.getint(child)
            elif tagn == "findlist":
                for sub in child:
                    res = FindRes()
                    res.load(sub)
                    self.findlist.append(res)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.filename is not None:
            xmlutil.savedata(doc, node, "filename", self.filename)
        if self.obsind is not None:
            xmlutil.savedata(doc, node, "obsind", self.obsind)
        if self.fitsind is not None:
            xmlutil.savedata(doc, node, "fitsind", self.fitsind)
        if self.number_results() != 0:
            flnode = ET.SubElement(node, "findlist")
            for l in self.get_list():
                l.save(doc, flnode, "findres")

def load(filename):
    """Load restults from file"""
    try:
        doc, root = xmlutil.load_file(filename, "findresults")
        fnode = xmlutil.find_child(root, "findresset")
    except xmlutil.XMLError as e:
        raise FindResError(e.args[0])
    result = FindResSet()
    result.load(fnode)
    return result

def save(filename, res):
    """Save results to file"""
    doc, root = xmlutil.init_save("FINDRESULTS", "findresults")
    res.save(doc, root, "findresset")
    xmlutil.complete_save(filename, doc)
