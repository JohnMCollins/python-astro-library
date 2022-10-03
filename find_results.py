"""Classes for reesult finding as XML"""

import os.path
import math
import xml.etree.ElementTree as ET
import numpy as np
import scipy.optimize as opt
import xmlutil
import remdefaults
import objident
import objdata
import gauss2d

# import sys

FINDRES_DOC_ROOT = "Findres2"

DEFAULT_SIGN = 1.5
DEFAULT_TOTSIGN = .75


class FitResult:
    """Class for remembering closeness of fit for finding algorithms"""

    def __init__(self, row, col, rowdiff=0, coldiff=0, apsize = 0.0, adus=0.0, peak=0.0, fitpeak=1.0, fitsigma=1.0, peakstd=0.0, sigmastd=0.0):
        self.row = row
        self.col = col
        self.rowdiff = rowdiff
        self.coldiff = coldiff
        self.apsize = apsize
        self.adus = adus
        self.peak = peak
        self.fitpeak = fitpeak
        self.fitsigma = fitsigma
        self.peakstd = peakstd
        self.sigmastd = sigmastd
        self.combined_sig = (peakstd * sigmastd) / (fitpeak * fitsigma)
        self.meanadus = 1.0             # Used in opt_aperture


class FindResultErr(Exception):
    """"Throw if error faound"""


class FindResult:
    """Class for remembering a single result"""

    Field_names = dict(radeg=xmlutil.getfloat,
                       decdeg=xmlutil.getfloat,
                       col=xmlutil.getint,
                       row=xmlutil.getint,
                       apsize=xmlutil.getfloat,
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
        self.apsize = 0.0
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
            self.obj.check_valid_id()
        except AttributeError:
            return  True
        except objident.ObjIdentErr:
            return  True
        return  False

    def is_usable(self):
        """Report if object is usable as far as we know"""
        return  self.obj is None or self.obj.usable

    def assign_label(self, dbcurs, existing_labs):
        """Assign a permanent label to the result, avoiding the existing labels"""
        if  not self.is_usable() or self.not_identified():
            raise  FindResultErr("Object not usable")
        n = 0
        base = ord('A')
        while 1:
            nlab = chr(base + n % 26)
            if n >= 26:
                nlab += str(n // 26)
            if nlab not in existing_labs:
                break
            n += 1
        self.obj.label = self.label = nlab
        existing_labs.add(nlab)
        return  dbcurs.execute("UPDATE objdata SET label=%s WHERE ind={:d}".format(self.obj.objind), nlab)

    def unassign_label(self, dbcurs):
        """Unassing permanent label from the result"""
        if  not self.is_usable() or self.not_identified():
            raise  FindResultErr("Object not usable")
        self.obj.label = None
        self.label = 'zzz'
        return  dbcurs.execute("UPDATE objdata SET label=NULL WHERE ind={:d}".format(self.obj.objind))

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
        self.apsize = 0.0
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

        # For excluding single pixels

        ar = range(-1,2)
        spx, spy = np.meshgrid(ar, ar)
        self.spmask = ((spx!=0)|(spy!=0)).astype(np.float64)

        # Working variables only for benefit of searches

        self.imagedata = self.maskbool = self.mask = self.xypoints = None
        self.pixrows = self.pixcols = self.minrow = self.mincol = self.maxrow = self.maxcol = 0
        self.maskpoints = self.skylevpoints = self.min_singlepix = self.min_apertureadus = 0.0
        self.exprow = self.expcol = self.currentap = self.currentiap = self.apsq = 0

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
        base = ord('a')
        for r in self.resultlist:
            if not r.obj.valid_label() or r.not_identified():
                l = chr(base + n % 26)
                if n >= 26:
                    l += str(n // 26)
                r.label = l
                n += 1
            else:
                r.label = r.obj.label

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

    def get_label_set(self, dbcurs):
        """Return set of existing permanent labels"""
        targobj = self.get_targobj()
        if  targobj is None:
            raise FindResultErr("No target in results")
        dbcurs.execute("SELECT label FROM objdata WHERE label IS NOT NULL AND vicinity=%s", targobj.obj.objname)
        elabrows = dbcurs.fetchall()
        return  {r[0] for r in elabrows}

    def get_image_dims(self, apsize):
        """Internal routine to get dimensions and other data of image"""

        if self.remfitsobj is None:
            raise FindResultErr("No image specified")
        self.imagedata = self.remfitsobj.data
        self.pixrows, self.pixcols = self.imagedata.shape

        self.currentap = apsize
        self.currentiap = int(math.floor(apsize))
        self.apsq = apsize ** 2
        self.minrow = self.mincol = self.currentiap + 1
        self.maxrow = self.pixrows - self.currentiap  # This is actually 1 more
        self.maxcol = self.pixcols - self.currentiap  # This is actually 1 more

    def make_ap_mask(self, apsize=None):
        """Make a mask of right size only for aperature of given radius"""

        if apsize is None:
            apsize = self.currentap
        iapsize = int(math.floor(apsize))
        xpoints, ypoints = np.meshgrid(range(-iapsize, iapsize + 1), range(-iapsize, iapsize + 1))
        radsq = apsize * apsize
        xsq = xpoints ** 2
        ysq = ypoints ** 2
        maskbool = xsq + ysq <= radsq
        self.mask = maskbool.astype(np.float64)
        self.maskbool = maskbool.flatten()
        # self.xpoints = xpoints.flatten()[maskbool]
        # self.ypoints = ypoints.flatten()[maskbool]
        self.xypoints = (xpoints.flatten()[self.maskbool], ypoints.flatten()[self.maskbool])
        self.maskpoints = np.count_nonzero(maskbool)
        self.skylevpoints = self.maskpoints * self.remfitsobj.meanval
        self.min_singlepix = self.remfitsobj.meanval + self.signif * self.remfitsobj.stdval
        self.min_apertureadus = self.maskpoints * self.remfitsobj.stdval * self.totsignif

    def get_aperture_data(self, row, column):
        """Get data in aperture according to mask"""
        halfside = self.currentiap + 1
        return  self.imagedata[row - self.currentiap:row + halfside, column - self.currentiap:column + halfside].flatten()[self.maskbool]

    def calculate_adus(self, row, column):
        """Calculate the total ADUs based arount the given row and column"""
        return  np.sum(self.get_aperture_data(row, column)) - self.skylevpoints

    def get_exp_rowcol(self, ra, dec):
        """Get expected row and column from given ra and dec"""
        expcol, exprow = self.remfitsobj.wcs.coords_to_colrow(ra, dec)
        self.exprow = int(round(exprow))
        self.expcol = int(round(expcol))

    def get_gauss_fit(self, row, column, rowdiff, coldiff):
        """Get Gasssian fit and fill in results structure"""
        dat = self.get_aperture_data(row, column) - self.remfitsobj.meanval
        peak = dat.max()
        adus = np.sum(dat)
        if adus < self.min_apertureadus:
            return  None

        try:
            (fitpeak, fitsigma), fit_errs = opt.curve_fit(gauss2d.gauss_circle, self.xypoints, dat, p0=(peak, self.remfitsobj.stdval))
        except RuntimeError:
            return  None

        if fitpeak <= 0  or fitsigma <= 0:
            return  None

        peakstd, sigmastd = np.sqrt(np.diag(fit_errs))
        return  FitResult(row, column, rowdiff=rowdiff, coldiff=coldiff,
                           apsize=self.currentap, adus=np.sum(dat), peak=peak,
                           fitpeak=fitpeak, fitsigma=fitsigma,
                           peakstd=peakstd, sigmastd=sigmastd)

    def get_object_offsets(self, searchp, maxshift=10, eoffrow=0, eoffcol=0):
        """Search the square given by the expected reow column at the centre with maxshift eiether side"""

        exprow = self.exprow - eoffrow
        expcol = self.expcol - eoffcol

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
            # If this is single pixel or close to it, don't bother
            if np.sum(self.imagedata[trow-1:trow+2,tcol-1:tcol+2] * self.spmask) <= searchp.singlepixn * self.min_singlepix:
                # print("Skipping single pixel at", tcol, trow)
                continue
            dat = self.get_gauss_fit(trow, tcol, exprow - trow, expcol - tcol)
            if dat is not None:
                results.append(dat)

        if len(results) == 0:
            return  None

        # Sort results by increasing distance from "origin", then by increasing fit (to make that most significant)

        results = sorted(results, key=lambda x: x.rowdiff**2 + x.coldiff**2)
        return  sorted(results, key=lambda x: x.combined_sig)

    def find_object(self, objloc, searchp, eoffrow=0, eoffcol=0, apsize=None, finding_target=False):
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
        maxs = searchp.maxshift2
        if finding_target:
            maxs = searchp.maxshift
        return  self.get_object_offsets(searchp, maxshift=maxs, eoffrow=eoffrow, eoffcol=eoffcol)

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
        return  self.get_object_offsets(searchp, maxshift=searchp.maxshift)

    def opt_aperture(self, row, col, searchp, minap=None, maxap=None, step=None):
        """Optimise aparture looking around either way from row and col,
        maximising aperture tbetween minap and maxap."""

        if minap is None:
            minap = searchp.minap
        if maxap is None:
            maxap = searchp.maxap
        if step is None:
            step = searchp.apstep
        results = []
        for possap in np.arange(minap, maxap + step, step):
            self.get_image_dims(possap)
            self.make_ap_mask(possap)
            # Store row offset, col offset, row, column, aperture, adus, adus per point
            for rtry in range(max(self.minrow, row - searchp.lookaround), min(self.maxrow, row + searchp.lookaround)):
                for ctry in range(max(self.mincol, col - searchp.lookaround), min(self.maxcol, col + searchp.lookaround)):
                    gfit = self.get_gauss_fit(rtry, ctry, rtry - row, ctry - col)
                    if gfit is not None:
                        gfit.meanadus = gfit.adus / self.maskpoints
                        results.append(gfit)

        # Choose firstly by best mean adus, then fit, then distance

        if len(results) == 0:
            return  None

        # This gets results by fit of signma with multilier

        results = sorted(results, key=lambda x: abs(x.fitsigma*searchp.totsig-x.apsize))

        topap = results[0].apsize
        results = [r for r in results if r.apsize == topap]

        results = sorted(results, key=lambda x: x.combined_sig)
        #results = sorted(results, key=lambda x:x.sigmastd)
        #
        # for r in results:
        #     print(r.apsize, r.adus, r.meanadus, r.combined_sig, r.fitpeak, r.fitsigma, r.peakstd, r.sigmastd)
        # r = results[0]
        # print("Final", r.apsize, r.adus, r.meanadus, r.combined_sig, r.fitpeak, r.fitsigma, r.peakstd, r.sigmastd)
        return  results[0]

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

#     def findbest_colrow(self, scol, srow, apsize, maxshift):
#         """Find the best column and row based on given starting column and row for given
#         aperture size, returning as (scol, srow, aducount, maxpoints)"""
#
#         self.get_image_dims(apsize)
#         self.makemask(apsize)
#
#         maxaduc = -1e6  # Hopefully anything will beat this
#         colmaxadu = scol
#         rowmaxadu = srow
#
#         for rs in range(max(self.minrow, srow - maxshift), min(self.maxrow, srow + maxshift)):
#             for cs in range(max(self.mincol, scol - maxshift), min(self.maxcol, scol + maxshift)):
#                 adu = np.sum(np.roll(np.roll(self.mask, shift=cs - self.mincol, axis=1), shift=rs - self.minrow, axis=0) * self.imagedata)
#                 if adu > maxaduc:
#                     maxaduc = adu
#                     rowmaxadu = rs
#                     colmaxadu = cs
#         if maxaduc < 0.0:
#             maxaduc = np.sum(np.roll(np.roll(self.mask, shift=scol - self.minrow, axis=1), shift=srow - self.minrow, axis=0) * self.imagedata)
#         return  (colmaxadu, rowmaxadu, maxaduc, self.maskpoints)

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
