"""General Class for locations of objloc list"""

import os.path
# import sys
import xml.etree.ElementTree as ET
import numpy as np
import xmlutil
import remdefaults
import objparam

OBJLOC_DOC_ROOT = "Objloc2"


class ObjLocErr(Exception):
    """"Throw if error faound"""


class ObjLoc(objparam.ObjParam):
    """Class for remembering an object location"""

    attr_routs = dict(row=xmlutil.getint, col=xmlutil.getint)

    def __init__(self, copyobj=None):
        super().__init__(copyobj=copyobj)
        self.col = None
        self.row = None
        self.istarget = self.is_target()

    def load(self, node):
        """Load from XNK dom"""
        self.load_param(node)
        self.col = None
        self.row = None
        self.istarget = xmlutil.getboolattr(node, "target")
        for child in node:
            tagn = child.tag
            try:
                setattr(self, tagn, ObjLoc.attr_routs[tagn](child))
            except KeyError:
                continue

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = self.save_param(doc, pnode, name)
        xmlutil.setboolattr(node, "target", self.istarget)
        for tagn in ObjLoc.attr_routs:
            val = getattr(self, tagn, None)
            if  val is not None:
                xmlutil.savedata(doc, node, tagn, val)
        return  node


class ObjLocs:
    """A class for grouping the above"""

    def __init__(self, remfitsobj=None):
        self.resultlist = []
        self.remfitsobj = remfitsobj
        self.obsdate = None
        self.filter = None
        self.obsind = None
        try:
            self.filter = remfitsobj.filter
            self.obsdate = remfitsobj.date
            self.obsind = remfitsobj.from_obsind
        except AttributeError:
            pass

    def add_loc(self, objd):
        """Add objdata to location"""
        self.resultlist.append(ObjLoc(copyobj=objd))

    def num_results(self):
        """Give number of results in list"""
        return len(self.resultlist)

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
            if res.origra is None or res.origdec is None:
                res.origra = res.ra
                res.origdec = res.dec
            res.ra, res.dec = coords

    def order_by_separation(self):
        """Sort objects in object list by descending order of separation
        from other objects treating declination degrees as twice the size as RA"""
        pl = [complex(r.ra, 2 * r.dec) for r in self.results()]
        dtab = np.abs(np.subtract.outer(pl, pl))
        for d in range(0, dtab.shape[0]):
            dtab[d, d] = 1e100
        # Find the minimum sepation from any other object in each case and sort
        # by maximum of that.
        self.resultlist = [self.resultlist[r] for r in np.argsort(-dtab.min(axis=1))]

    def get_offsets_in_image(self, forget_offsets=False):
        """Get row and column offsets in image for find results,
        return list of (col, row) corresponding to findresults list.
        col and row are -1 if not in the image
        Forget any existing offsets if forget_offsets is set"""

        if forget_offsets:
            self.remfitsobj.wcs.set_offsets(0, 0)
        coordlist = [(s.ra, s.dec) for s in self.results()]
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
        self.obsind = None
        self.filter = None
        self.resultlist = []

        for child in node:
            tagn = child.tag
            if tagn == "obsdate":
                self.obsdate = xmlutil.getdatetime(child)
            elif tagn == "obsind":
                self.obsind = xmlutil.getint(child)
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
            xmlutil.savedate(doc, node, "obsdate", self.obsdate)
        if self.obsind is not None and self.obsind != 0:
            xmlutil.savedata(doc, node, "obsind", self.obsind)
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
        dr = xmlutil.load_file(fname, OBJLOC_DOC_ROOT)
        root = dr[1]
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
