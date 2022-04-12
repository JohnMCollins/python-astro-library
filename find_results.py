"""Classes for reesult finding as XML"""

import os.path
import xml.etree.ElementTree as ET
import numpy as np
import xmlutil
import remdefaults
import objident
import objdata

# import sys

FINDRES_DOC_ROOT = "Findres2"

DEFAULT_SIGN = 1.5
DEFAULT_TOTSIGN = .75


class FindResultErr(Exception):
    """"Throw if error faound"""


class FindResult:
    """Class for remembering a single result"""

    Field_names = dict(radeg=xmlutil.getfloat,
                       decdeg=xmlutil.getfloat,
                       col=xmlutil.getint,
                       row=xmlutil.getint,
                       apsize=xmlutil.getint,
                       label=xmlutil.gettext,
                       adus=xmlutil.getfloat,
                       rdiff=xmlutil.getint,
                       cdiff=xmlutil.getint,
                       ident=None,
                       info=None,
                       mags=None,
                       position=None)

    def __init__(self, **kwargs):
        self.col = self.row = None
        self.adus = self.radeg = self.decdeg = 0.0
        self.rdiff = self.cdiff = 0
        self.apsize = 0
        self.obj = None
        self.label = ""
        self.istarget = False
        self.needs_correction = False
        self.hide = False
        for kw in tuple(FindResult.Field_names.keys()) + ('obj', 'hide'):
            try:
                setattr(self, kw, kwargs[kw])
            except KeyError:
                pass

    def not_identified(self):
        """Return if no identification"""
        try:
            self.obj.check_valid()
        except AttributeError:
            return  True
        except objident.ObjIdentErr:
            return  True
        return  False

    def is_usable(self):
        """Report if object is usable as far as we know"""
        return  self.obj is None or self.obj.usable

    def resetapsize(self, apsize=0, row=0, col=0, adus=0.0, rdiff=None, cdiff=None):
        """Reset result after recalculating aperture"""
        if row < 0 or col < 0:
            self.col = self.row = None
        else:
            self.col = col
            self.row = row
        if rdiff is not None:
            self.rdiff = rdiff
        if cdiff is not None:
            self.cdiff = cdiff
        self.apsize = apsize
        self.adus = adus
        self.radeg = self.decdeg = 0.0

    def load(self, node):
        """Load from XNK dom"""
        self.col = self.row = None
        self.rdiff = self.cdiff = 0
        self.apsize = 0
        self.radeg = self.decdeg = 0.0
        self.adus = 0.0
        self.label = ""
        self.obj = None
        self.hide = xmlutil.getboolattr(node, "hide")
        self.istarget = xmlutil.getboolattr(node, "target")
        self.needs_correction = xmlutil.getboolattr(node, "needsc")

        for child in node:
            tagn = child.tag
            try:
                lrout = FindResult.Field_names[tagn]
                if lrout is None:
                    if self.obj is None:
                        self.obj = objdata.ObjData()
                        self.obj.load(node)
                else:
                    setattr(self, tagn, lrout(child))
            except KeyError:
                pass

    def save(self, doc, pnode, name="result"):
        """Save to XML DOM node"""
        if self.obj is None:
            node = ET.SubElement(pnode, name)
        else:
            node = self.obj.save(doc, pnode, name)
        xmlutil.setboolattr(node, "target", self.istarget)
        xmlutil.setboolattr(node, "needsc", self.needs_correction)
        xmlutil.setboolattr(node, "hide", self.hide)
        for k, r in FindResult.Field_names.items():
            if r is None:
                continue
            v = getattr(self, k, None)
            if v is not None and (not isinstance(v, str) or len(v) != 0):
                xmlutil.savedata(doc, node, k, v)


class FindResults:
    """A class for remembering things we've found"""

    Fr_fields = dict(obsdate=xmlutil.getdatetime,
                     obsind=xmlutil.getint,
                     nrows=xmlutil.getint,
                     ncols=xmlutil.getint,
                     filter=xmlutil.gettext,
                     signif=xmlutil.getfloat,
                     totsignif=xmlutil.getfloat)

    def __init__(self, remfitsobj=None):
        self.resultlist = []
        self.remfitsobj = remfitsobj
        self.obsdate = None
        self.obsind = None
        self.filter = None
        self.nrows = None
        self.ncols = None
        self.totsignif = None
        self.signif = None
        self.objdict = dict()
        try:
            self.filter = remfitsobj.filter
            self.obsdate = remfitsobj.date
            self.obsind = remfitsobj.from_obsind
            self.nrows, self.ncols = remfitsobj.data.shape
        except AttributeError:
            pass

        # Working variables only for benefit of searches

        self.imagedata = self.mask = None
        self.pixrows = self.pixcols = self.minrow = self.mincol = self.maxrow = self.maxcol = 0
        self.maskpoints = self.skylevpoints = self.min_singlepix = self.min_apertureadus = 0.0
        self.exprow = self.expcol = self.currentap = self.apsq = 0

    def num_results(self, idonly=False, nohidden=False):
        """Return number of find results, if idonly is True, limit to ones identified"""
        if idonly:
            if nohidden:
                return len([r for r in self.resultlist if not r.hide and r.obj is not None])
            return len([r for r in self.resultlist if r.obj is not None])
        if nohidden:
            return len([r for r in self.resultlist if not r.hide])
        return  len(self.resultlist)

    def results(self, idonly=False, nohidden=False):
        """Generator for result list"""
        for r in self.resultlist:
            if (not idonly or r.obj is not None) and (not nohidden or not r.hide):
                yield r

    def __getitem__(self, k):
        try:
            if isinstance(k, str):
                return  self.objdict[k]
            return self.resultlist[k]
        except (IndexError, KeyError):
            raise FindResultErr("Cannot find item " + str(k) + " in find results")

    def tooclose(self, row, col, existing):
        """Reject possible if too close to existing one"""

        for r, c, dummy in existing:
            if (r - row) ** 2 + (c - col) ** 2 <= 4 * self.apsq:
                return True
        return False

    def get_targobj(self):
        """Get target object, which we assume to be sorted to the front"""
        if self.num_results(idonly=True, nohidden=True) == 0:
            return  None
        ret = self.resultlist[0]
        if ret.hide or not ret.istarget:
            return  None
        return  ret

    def relabel(self):
        """Assign labels to reordered list"""
        n = 0
        base = ord('A')
        for r in self.resultlist:
            l = chr(base + n % 26)
            if n >= 26:
                l += str(n // 26)
            r.label = l
            n += 1

    def rekey(self):
        """Recreate the lookup table"""
        self.objdict = dict()
        for r in self.results():
            if r.obj is not None:
                self.objdict[r.obj.objname] = r
            self.objdict[r.label] = r

    def reorder(self):
        """Reorder fesult list to take account of changed aperture/results"""

        self.resultlist = [r for r in self.resultlist if r.col is not None and r.row is not None]
        self.resultlist.sort(key=lambda x: x.adus + int(x.istarget) * 1e50, reverse=True)

    def get_image_dims(self, apsize):
        """Internal routine to get dimensions and other data of image"""

        if self.remfitsobj is None:
            raise FindResultErr("No image specified")
        self.imagedata = self.remfitsobj.data
        self.pixrows, self.pixcols = self.imagedata.shape

        self.currentap = apsize
        self.apsq = apsize ** 2
        self.minrow = self.mincol = apsize + 1
        self.maxrow = self.pixrows - apsize  # This is actually 1 more
        self.maxcol = self.pixcols - apsize  # This is actually 1 more

    def makemask(self, apsize):
        """Make a mask for aperature of given radius"""

        self.currentap = apsize
        self.mask = np.zeros_like(self.imagedata)
        rads = np.add.outer((np.arange(0, self.pixrows) - apsize) ** 2, (np.arange(0, self.pixcols) - apsize) ** 2)
        rv, cv = np.where(rads <= apsize * apsize)
        for r, c in zip(rv, cv):
            self.mask.itemset((r, c), 1.0)
        self.maskpoints = np.sum(self.mask)
        self.skylevpoints = self.maskpoints * self.remfitsobj.meanval
        self.min_singlepix = self.remfitsobj.meanval + self.signif * self.remfitsobj.stdval
        self.min_apertureadus = self.maskpoints * self.remfitsobj.stdval * self.totsignif

    def make_ap_mask(self, apsize=None):
        """Make a mask of right size only for aperature of given radius"""

        if apsize is None:
            apsize = self.currentap
        side = apsize * 2 + 1
        radsq = apsize * apsize
        self.mask = np.zeros((side, side), dtype=np.float32)
        for r in range(side):
            for c in range(side):
                if (r - apsize) ** 2 + (c - apsize) ** 2 <= radsq:
                    self.mask.itemset((r, c), 1.0)

        self.maskpoints = np.sum(self.mask)
        self.skylevpoints = self.maskpoints * self.remfitsobj.meanval
        self.min_singlepix = self.remfitsobj.meanval + self.signif * self.remfitsobj.stdval
        self.min_apertureadus = self.maskpoints * self.remfitsobj.stdval * self.totsignif

    def calculate_adus(self, row, column):
        """Calculate the total ADUs based arount the given row and column"""
        halfside = self.currentap + 1  # as we have width + 1 + width
        return  np.sum(self.mask * self.imagedata[row - self.currentap:row + halfside, column - self.currentap:column + halfside]) - self.skylevpoints

    def get_exp_rowcol(self, ra, dec):
        """Get expected row and column from given ra and dec"""
        expcol, exprow = self.remfitsobj.wcs.coords_to_pix(((ra, dec),))[0]
        self.exprow = int(round(exprow))
        self.expcol = int(round(expcol))

    def get_object_offsets(self, maxshift=10, eoffrow=0, eoffcol=0):
        """Search the square given by the expected reow column at the centre with maxshift eiether side"""

        exprow = self.exprow + eoffrow
        expcol = self.expcol + eoffcol

        # First pass is to list points in region at least as much as to make a single pixel
        # more than the minimum for one pixel

        startrow = max(exprow - maxshift, self.minrow)
        startcol = max(expcol - maxshift, self.mincol)
        trows, tcols = np.where(self.imagedata[startrow:min(exprow + maxshift, self.maxrow), startcol:min(expcol + maxshift, self.maxcol)] >= self.min_singlepix)

        # If we didn't find anything, give up

        if len(trows) == 0:
            return  None

        # add back the start row and col

        trows += startrow
        tcols += startcol

        # Return results as row offset (to add to eoffrow) col offset (ditto), row, column, adus

        results = []

        for trow, tcol in zip(trows, tcols):
            dat = self.calculate_adus(trow, tcol)
            if dat >= self.min_apertureadus:
                results.append((trow - exprow, tcol - expcol, trow, tcol, dat))

        if len(results) == 0:
            return  None

        # Sort results by increasing distance from "origin", then by decreasing ADUs

        return  sorted(sorted(results, key=lambda x: x[0] ** 2 + x[1] ** 2), reverse=True, key=lambda x: x[-1])

    def find_object(self, objloc, searchp, eoffrow=0, eoffcol=0, apsize=None):
        """Fins specific object from expected"""
        if apsize is None:
            apsize = objloc.apsize
            if apsize == 0:
                apsize = searchp.defapsize
        self.get_image_dims(apsize)
        self.totsignif = searchp.totsig
        self.signif = searchp.signif
        self.make_ap_mask(apsize)
        self.exprow = objloc.row
        self.expcol = objloc.col
        return  self.get_object_offsets(maxshift=searchp.maxshift, eoffrow=eoffrow, eoffcol=eoffcol)

    def find_peak(self, row, col, searchp, apsize=None):
        """Find peak for when we are giving a label to an object"""
        if apsize is None:
            apsize = searchp.defapsize
        self.get_image_dims(apsize)
        self.totsignif = searchp.totsig
        self.signif = searchp.signif
        self.make_ap_mask(apsize)
        self.exprow = row
        self.expcol = col
        return  self.get_object_offsets(maxshift=searchp.maxshift)

    def opt_aperture(self, row, col, searchp, minap=None, maxap=None):
        """Optimise aparture looking around either way from row and col,
        maximising aperture tbetween minap and maxap."""

        if minap is None:
            minap = searchp.minap
        if maxap is None:
            maxap = searchp.maxap
        results = []
        for possap in range(minap, maxap + 1):
            self.get_image_dims(possap)
            self.make_ap_mask(possap)
            # Store row offset, col offset, row, column, aperture, adus, adus per point
            for rtry in range(max(self.minrow, row - searchp.lookaround), min(self.maxrow, row + searchp.lookaround)):
                for ctry in range(max(self.mincol, col - searchp.lookaround), min(self.maxcol, col + searchp.lookaround)):
                    adus = self.calculate_adus(rtry, ctry)
                    results.append((rtry - row, ctry - col, rtry, ctry, possap, adus, adus / self.maskpoints))

        results = sorted(sorted(results, key=lambda x: x[0] ** 2 + x[1] ** 2), reverse=True, key=lambda x: x[-1])
        dummy, dummy, rres, cres, aperture, adus, dummy = results[0]
        return  (aperture, rres, cres, adus)

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

        self.get_image_dims(apsize)
        self.makemask(apsize)

        maxaduc = -1e6  # Hopefully anything will beat this
        colmaxadu = scol
        rowmaxadu = srow

        for rs in range(max(self.minrow, srow - maxshift), min(self.maxrow, srow + maxshift)):
            for cs in range(max(self.mincol, scol - maxshift), min(self.maxcol, scol + maxshift)):
                adu = np.sum(np.roll(np.roll(self.mask, shift=cs - self.mincol, axis=1), shift=rs - self.minrow, axis=0) * self.imagedata)
                if adu > maxaduc:
                    maxaduc = adu
                    rowmaxadu = rs
                    colmaxadu = cs
        if maxaduc < 0.0:
            maxaduc = np.sum(np.roll(np.roll(self.mask, shift=scol - self.minrow, axis=1), shift=srow - self.minrow, axis=0) * self.imagedata)
        return  (colmaxadu, rowmaxadu, maxaduc, self.maskpoints)

    def load(self, node):
        """Load up from XML dom"""

        self.obsdate = None
        self.obsind = None
        self.nrows = self.ncols = None
        self.filter = None
        self.resultlist = []
        self.signif = None
        self.totsignif = None

        for child in node:
            tagn = child.tag
            try:
                setattr(self, tagn, FindResults.Fr_fields[tagn](child))
            except KeyError:
                if tagn == "results":
                    for gc in child:
                        fr = FindResult()
                        fr.load(gc)
                        self.resultlist.append(fr)
        self.rekey()

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        for k in FindResults.Fr_fields:
            v = getattr(self, k, None)
            if v is not None:
                xmlutil.savedata(doc, node, k, v)
        if len(self.resultlist) != 0:
            gc = ET.SubElement(node, "results")
            for fr in self.results():
                fr.save(doc, gc, "result")


def load_results_from_file(fname, fitsobj=None, oknotfound=False):
    """Load results from results text file"""
    fname = remdefaults.findres_file(fname)
    try:
        dummy, root = xmlutil.load_file(fname, FINDRES_DOC_ROOT, oknotfound)
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
    filename = remdefaults.findres_file(filename)
    if not force and os.path.exists(filename):
        raise FindResultErr("Will not overwrite existing file " + filename)
    try:
        doc, root = xmlutil.init_save(FINDRES_DOC_ROOT, FINDRES_DOC_ROOT)
        results.save(doc, root, "RES")
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise FindResultErr("Save of " + filename + " gave " + e.args[0])
