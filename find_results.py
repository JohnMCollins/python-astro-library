# General Class for find results
# We may update these to use XML or possibly the database

import numpy as np
import miscutils
import os.path
import xml.etree.ElementTree as ET
import xmlutil
import datetime
# import sys

FINDRES_DOC_ROOT = "Findres"


class FindResultErr(Exception):
    """"Throw if error faound"""
    pass


class FindResult(object):
    """Class for remembering a single result"""

    def __init__(self, radeg=0.0, decdeg=0.0, apsize=0, col=None, row=None, label="", name="", adus=0.0, istarget=False):
        self.radeg = radeg
        self.decdeg = decdeg
        self.col = col
        self.row = row
        self.apsize = apsize
        self.name = name
        self.label = label
        self.adus = adus
        self.istarget = istarget

    def resetapsize(self, apsize=0, row=0, col=0, adus=0.0):
        """Reset result after recalculating aperture"""
        if row < 0 or col < 0:
            self.col = self.row = None
        else:
            self.col = col
            self.row = row
        self.apsize = apsize
        self.adus = adus
        self.radeg = self.decdeg = 0.0

    def load(self, node):
        """Load from XNK dom"""
        self.radeg = 0.0
        self.decdeg = 0.0
        self.col = None
        self.row = None
        self.apsize = 0
        self.name = ""
        self.label = ""
        self.adus = 0.0
        self.istarget = node.get("target", False)
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
            elif tagn == "apsize":
                self.apsize = xmlutil.getint(child)
            elif tagn == "name":
                self.name = xmlutil.gettext(child)
            elif tagn == "label":
                self.label = xmlutil.gettext(child)
            elif tagn == "adus":
                self.adus = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.istarget:
            node.set("target", "y")
        if self.radeg != 0.0:
            xmlutil.savedata(doc, node, "radeg", self.radeg)
        if self.decdeg != 0.0:
            xmlutil.savedata(doc, node, "decdeg", self.decdeg)
        if self.col is not None:
            xmlutil.savedata(doc, node, "col", self.col)
        if self.row is not None:
            xmlutil.savedata(doc, node, "row", self.row)
        if self.apsize != 0:
            xmlutil.savedata(doc, node, "apsize", self.apsize)
        if len(self.name) != 0:
            xmlutil.savedata(doc, node, "name", self.name)
        if len(self.label) != 0:
            xmlutil.savedata(doc, node, "label", self.label)
        if self.adus != 0.0:
            xmlutil.savedata(doc, node, "adus", self.adus)


class FindResults(object):
    """A class for remembering things we've found"""

    def __init__(self, remfitsobj=None):
        self.resultlist = []
        self.apsq = 0
        self.remfitsobj = remfitsobj
        try:
            self.obsdate = remfitsobj.date
        except AttributeError:
            self.obsdate = None

    def results(self):
        """Generator for result list"""
        for r in self.resultlist:
            yield r

    def tooclose(self, row, col, existing):
        """Reject possible if too close to existing one"""

        for r, c, adu in existing:
            if (r - row) ** 2 + (c - col) ** 2 <= 4 * self.apsq:
                return True
        return False

    def relabel(self):
        """Assign labels to reordered list"""
        lng = len(self.resultlist)
        n = 0
        for r in self.resultlist:
            try:
                r.label = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijlmnopqrstuvwxyz"[n]
            except IndexError:
                r.label = "Obj%.3d" % n
            n += 1

    def reorder(self):
        """Reorder fesult list to take account of changed aperture/results"""

        self.resultlist = [r for r in self.resultlist if r.col is not None and r.row is not None]
        self.resultlist.sort(key=lambda x: x.adus, reverse=True)

    def makemask(self, apwidth):
        """Make a mask for aperature of given radius"""

        sqrad = apwidth ** 2
        mask = np.zeros_like(self.remfitsobj.data)
        pixrows, pixcols = mask.shape
        rads = np.add.outer((np.arange(0, pixrows) - apwidth) ** 2, (np.arange(0, pixcols) - apwidth) ** 2)
        rv, cv = np.where(rads <= sqrad)
        for r, c in zip(rv, cv):
            mask.itemset((r, c), 1.0)
        return  mask

    def findfast(self, sign=10.0, apwidth=6, totsign=5.0, brightestonly=1000000, ignleft=0, ignright=0, igntop=0, ignbottom=0):
        """Find x,y coods and adus of objects in image data.

        Sign gives the number of standard deviations multiple to look for
        apwidth gives width of aperture to start from

        We reject possibles whose total comes to less than totsign * stddevs
        return the number of results we found.
        Limit to number given in brightestonly if only interested in those.
        """

        if self.remfitsobj is None:
            raise FindResultErr("No image specified")

        imagedata = self.remfitsobj.data
        pixrows, pixcols = imagedata.shape

        apdiam = 2 * apwidth + 1
        self.apsq = apwidth ** 2
        mincol = minrow = apwidth - 1
        startcol = ignleft + mincol
        startrow = ignbottom + minrow
        maxrow = pixrows - apdiam - igntop  # This is actually 1 more
        maxcol = pixcols - apdiam - ignbottom  # This is actually 1 more
        # print("Rows %d to %d cols %d to %d" % (minrow, maxrow, mincol, maxcol), file=sys.stderr)

        # Kick off with masj ub bottom left

        mask = self.makemask(apwidth)
        points = np.sum(mask)
        skylevpoints = points * self.remfitsobj.meanval
        cutoff = points * totsign * self.remfitsobj.stdval

        # Get list of points greater than n std devs within search area

        flatim = imagedata[startrow:maxrow, startcol:maxcol].flatten()
        flatim = flatim[flatim > self.remfitsobj.meanval + sign * self.remfitsobj.stdval]
        flatim = -np.unique(-flatim)

        # print("Number of max values is", flatim.shape[0], file=sys.stderr)
        rows = []
        cols = []
        sums = []

        for mxv in flatim:
            wr, wc = np.where(imagedata == mxv)
            # print("%d values matched %.2f" % (len(wr), mxv), file=sys.stderr)
            for r, c in zip(wr, wc):
                if r < startrow or r >= maxrow:
                    # print("row %d outside range" % r, file=sys.stderr)
                    continue
                if c < startcol or c >= maxcol:
                    # print("col %d outside range" % c, file=sys.stderr)
                    continue
                adu = np.sum(np.roll(np.roll(mask, shift=c - mincol, axis=1), shift=r - minrow, axis=0) * imagedata) - skylevpoints
                if adu < cutoff:
                    # print("ADU count of %2f less than cutoff of %.4f" % (adu, cutoff), file=sys.stderr)
                    continue
                rows.append(r)
                cols.append(c)
                sums.append(adu)

        possibles = [ (rows[n], cols[n], sums[n]) for n in (-np.array(sums)).argsort() ]

        results = []
        for r, c, adu in possibles:
            if self.tooclose(r, c, results):
                continue
            results.append((r, c, adu))

        self.resultlist = []
        for r, c, adu in sorted(results, key=lambda x:x[2], reverse=True):
            self.resultlist.append(FindResult(row=r, col=c, apsize=apwidth, adus=adu))
            if len(self.resultlist) >= brightestonly:
                break

        if len(self.resultlist) != 0:
            self.calccoords()
            self.relabel()
        return  len(self.resultlist)

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
                r = c = -1
            else:
                c = int(round(c))
                r = int(round(r))
            result.append((c, r))
            res.col = c
            res.row = r
        return  result

    def findbest_colrow(self, scol, srow, apsize, maxshift):
        """Find the best column and row based on given starting column and row for given
        aperture size, returning as (scol, srow, aducount, maxpoints)"""

        imagedata = self.remfitsobj.data
        pixrows, pixcols = imagedata.shape
        mask = self.makemask(apsize)
        points = np.sum(mask)
        apdiam = 2 * apsize + 1
        mincol = minrow = apsize - 1
        maxrow = pixrows - apdiam  # This is actually 1 more
        maxcol = pixcols - apdiam  # This is actually 1 more

        maxaduc = -1e6  # Hopefully anything will beat this

        for rs in range(max(minrow, srow - maxshift), min(maxrow, srow + maxshift)):
            for cs in range(max(mincol, scol - maxshift), min(maxcol, scol + maxshift)):
                adu = np.sum(np.roll(np.roll(mask, shift=cs - mincol, axis=1), shift=rs - minrow, axis=0) * imagedata)
                if adu > maxaduc:
                    maxaduc = adu
                    rowmaxadu = rs
                    colmaxadu = cs
        return  (colmaxadu, rowmaxadu, maxaduc, np.sum(mask))

    def load(self, node):
        """Load up from XML dom"""

        self.obsdate = None
        self.resultlist = []

        for child in node:
            tagn = child.tag
            if tagn == "obsdate":
                self.obsdate = datetime.datetime.fromisoformat(xmlutil.gettext(child))
            elif tagn == "results":
                for gc in child:
                    fr = FindResult()
                    fr.load(gc)
                    self.resultlist.append(fr)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.obsdate is not None:
            xmlutil.savedata(doc, node, "obsdate", self.obsdate.isoformat())
        if len(self.resultlist) != 0:
            gc = ET.SubElement(node, "results")
            for fr in self.results():
                fr.save(doc, gc, "result")


def load_results_from_file(fname, fitsobj=None):
    """Load results from results text file"""
    fname = miscutils.replacesuffix(fname, ".findres")
    try:
        doc, root = xmlutil.load_file(fname, FINDRES_DOC_ROOT)
        fr = FindResults(fitsobj)
        frnode = root.find("RES")
        if frnode is None:
            raise xmlutil.XMLError("No tree")
        fr.load(frnode)
    except xmlutil.XMLError as e:
        raise FindResultErr("Load of " + fname + " gave " + e.args[0])
    return  fr


def save_results_to_file(results, filename, force=False):
    """Save results to results text file"""
    filename = miscutils.replacesuffix(filename, ".findres")
    if not force and os.path.exists(filename):
        raise FindResultErr("Will not overwrite existing file " + filename)
    try:
        doc, root = xmlutil.init_save(FINDRES_DOC_ROOT, FINDRES_DOC_ROOT)
        results.save(doc, root, "RES")
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise FindResultErr("Save of " + fname + " gave " + e.args[0])
