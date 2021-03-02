"""General Class for locations of objloc list"""

import os.path
import datetime
import xml.etree.ElementTree as ET
import numpy as np
import xmlutil
import remdefaults
# import sys

OBJLOC_DOC_ROOT = "Objloc"


class ObjLocErr(Exception):
    """"Throw if error faound"""


class ObjLoc:
    """Class for remembering an object location"""

    def __init__(self, radeg=0.0, decdeg=0.0, col=0, row=0, name="", dispname="", apsize=6, istarget=False, invented=False, isusable=True):
        self.radeg = radeg
        self.decdeg = decdeg
        self.col = col
        self.row = row
        self.name = name
        self.dispname = dispname
        self.apsize = apsize
        self.istarget = istarget
        self.invented = invented
        self.isusable = isusable

    def load(self, node):
        """Load from XNK dom"""
        self.radeg = 0.0
        self.decdeg = 0.0
        self.col = 0
        self.row = 0
        self.name = ""
        self.dispname = ""
        self.apsize = 6
        self.istarget = node.get("target", 'n') == 'y'
        self.invented = node.get("invented", 'n') == 'y'
        self.isusable = node.get("unusable", 'n') != 'y'
        for child in node:
            tagn = child.tag
            if tagn == "radeg":
                self.radeg = xmlutil.getfloat(child)
            elif tagn == "decdeg":
                self.decdeg = xmlutil.getfloat(child)
            elif tagn == "col":
                self.col = xmlutil.getint(child)
            elif tagn == "row":
                self.row = xmlutil.getint(child)
            elif tagn == "name":
                self.name = xmlutil.gettext(child)
            elif tagn == "dispname":
                self.dispname = xmlutil.gettext(child)
            elif tagn == "apsize":
                self.apsize = xmlutil.getint(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.istarget:
            node.set("target", "y")
        if self.invented:
            node.set("invented", "y")
        if not self.isusable:
            node.set("unusable", "y")
        if self.radeg != 0.0:
            xmlutil.savedata(doc, node, "radeg", self.radeg)
        if self.decdeg != 0.0:
            xmlutil.savedata(doc, node, "decdeg", self.decdeg)
        if self.col is not None:
            xmlutil.savedata(doc, node, "col", self.col)
        if self.row is not None:
            xmlutil.savedata(doc, node, "row", self.row)
        if len(self.name) != 0:
            xmlutil.savedata(doc, node, "name", self.name)
        if len(self.dispname) != 0:
            xmlutil.savedata(doc, node, "dispname", self.dispname)
        xmlutil.savedata(doc, node, "apsize", self.apsize)


class ObjLocs:
    """A class for grouping the above"""

    def __init__(self, remfitsobj=None):
        self.resultlist = []
        self.remfitsobj = remfitsobj
        self.obsdate = None
        self.filter = None
        try:
            self.filter = remfitsobj.filter
            self.obsdate = remfitsobj.date
        except AttributeError:
            pass

    def add_loc(self, objd):
        """Add objdata to location"""
        r = ObjLoc(radeg=objd.ra, decdeg=objd.dec, name=objd.objname, dispname=objd.dispname, istarget=objd.is_target(), apsize=objd.apsize, isusable=objd.usable, invented=objd.invented)
        self.resultlist.append(r)

    def results(self):
        """Generator for result list"""
        for r in self.resultlist:
            yield r

    def calccoords(self):
        """Converts rows and columns in result list to ra and dec"""

        w = self.remfitsobj.wcs
        rowcols = []

        for res in self.results():
            rowcols.append((res.col, res.row))

        coordlist = w.pix_to_coords(np.array(rowcols))

        for res, coords in zip(self.results(), coordlist):
            res.radeg, res.decdeg = coords

    def get_offsets_in_image(self):
        """Get row and column offsets in image for find results,
        return list of (col, row) corresponding to findresults list.
        col and row are -1 if not in the image"""

        coordlist = [(s.radeg, s.decdeg) for s in self.results()]
        pixlist = self.remfitsobj.wcs.coords_to_pix(np.array(coordlist))
        pixrows, pixcols = self.remfitsobj.data.shape
        result = []
        for cr, res in zip(pixlist, self.results()):
            c, r = cr
            if c < 0 or r < 0 or c > pixcols or r > pixrows:
                continue
            c = int(round(c))
            r = int(round(r))
            res.col = c
            res.row = r
            result.append(res)
        if len(result) != len(self.resultlist):
            self.resultlist = result

    def load(self, node):
        """Load up from XML dom"""

        self.obsdate = None
        self.filter = None
        self.resultlist = []

        for child in node:
            tagn = child.tag
            if tagn == "obsdate":
                self.obsdate = datetime.datetime.fromisoformat(xmlutil.gettext(child))
            elif tagn == 'filter':
                self.filter = xmlutil.gettext(child)
            elif tagn == "objlist":
                for gc in child:
                    fr = ObjLoc()
                    fr.load(gc)
                    self.resultlist.append(fr)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.obsdate is not None:
            xmlutil.savedata(doc, node, "obsdate", self.obsdate.isoformat())
        if self.filter is not None:
            xmlutil.savedata(doc, node, "filter", self.filter)
        if len(self.resultlist) != 0:
            gc = ET.SubElement(node, "objlist")
            for fr in self.results():
                fr.save(doc, gc, "result")


def load_objlist_from_file(fname, fitsobj=None):
    """Load results from objloc XML file"""
    fname = remdefaults.objloc_file(fname)
    try:
        doc, root = xmlutil.load_file(fname, OBJLOC_DOC_ROOT)
        fr = ObjLocs(fitsobj)
        frnode = root.find("LOCS")
        if frnode is None:
            raise xmlutil.XMLError("No tree")
        fr.load(frnode)
    except xmlutil.XMLError as e:
        raise ObjLocErr("Load of " + fname + " gave " + e.args[0])
    return  fr


def save_objlist_to_file(results, filename, force=False):
    """Save results to objloc XNL file"""
    filename = remdefaults.objloc_file(filename)
    if not force and os.path.exists(filename):
        raise ObjLocErr("Will not overwrite existing file " + filename)
    try:
        doc, root = xmlutil.init_save(OBJLOC_DOC_ROOT, OBJLOC_DOC_ROOT)
        results.save(doc, root, "LOCS")
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise ObjLocErr("Save of " + filename + " gave " + e.args[0])