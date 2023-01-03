"""Classes for reesult finding as XML"""

import math
# import sys
import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib import colors
import scipy.optimize as opt
import objident
import objdata
import gauss2d

FINDRES_DOC_ROOT = "Findres2"

DEFAULT_SIGN = 1.5
DEFAULT_TOTSIGN = .75

class FitResult:
    """Class for remembering closeness of fit for finding algorithms"""

    def __init__(self, row, col, rowdiff=0.0, coldiff=0.0, apsize = 0.0, adus=0.0, modadus = 0.0, peak=0.0, fitpeak=1.0, fitsigma=1.0, peakstd=0.0, sigmastd=0.0):
        self.row = row
        self.col = col
        self.rowdiff = rowdiff
        self.coldiff = coldiff
        self.apsize = apsize
        self.adus = adus
        self.modadus = modadus
        self.peak = peak
        self.fitpeak = fitpeak
        self.fitsigma = fitsigma
        self.peakstd = peakstd
        self.sigmastd = sigmastd


class FindResultErr(Exception):
    """"Throw if error faound"""


class FindResult:
    """Class for remembering a single result"""

    frfields = dict(obsind='d', objind='d', ind='Z', nrow='f', ncol='f', rdiff='f', cdiff='f',
                    radeg='f', decdeg='f', amp='f', sigma='f', ampstd='f', sigmastd='f', apsize='f',
                    adus='f', modadus='f', hide='b')
    frformats = dict(d='{:d}', f="{:.16e}", b="{:d}")

    def __init__(self, obj = None, objind = None, apsize = 0.0, ind = None):
        self.obsind = self.col = self.row = None
        self.radeg = self.decdeg = self.rdiff = self.cdiff = 0.0
        self.amp = self.sigma = self.ampstd = self.sigmastd = self.adus = self.modadus = 0.0
        self.obj = None
        self.label = ""
        self.istarget = self.hide = False
        self.ind = ind
        self.obj = obj
        self.objind = objind
        self.apsize = apsize
        if obj is not None:
            self.objind = obj.objind
            if obj.valid_label():
                self.label = obj.label
            if apsize == 0.0:
                self.apsize = obj.apsize

    def not_identified(self):
        """Return if no identification"""
        try:
            self.obj.check_valid_id()
        except AttributeError:
            return  True
        except objident.ObjIdentErr:
            return  True
        return  False

    def calculate_mod_integral(self, apsize = None):
        """Calculate model-based adus"""
        if apsize is None:
            apsize = self.apsize
        if  self.sigma == 0.0 or apsize == 0.0:
            return  0.0
        return  self.amp * 2.0 * np.pi * (1.0 - self.sigma**2 * math.exp((apsize/self.sigma)**2 / -2.0))

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

    def loaddb(self, dbcurs, obj = None, ind = None, objind = None, obsind = None):
        """Load record from database by ind or objind and obsind"""
        self.obj = obj
        if obj is not None:
            ind = obj.objind
        if ind is not None:
            Wh = "ind={:d}".format(ind)
        else:
            try:
                Wh = "objind={:d} AND obsind={:d}".format(objind, obsind)
            except TypeError:
                raise FindResultErr("Attempting to load findresult with no objind and obsind")
        fields = FindResult.frfields.keys()
        dbcurs.execute("SELECT " + ",".join(fields) + " FROM findresult WHERE " + Wh)
        r = dbcurs.fetchone()
        if r is None:
            raise FindResultErr("Expecting findresult record")
        for f,val in zip(fields,r):
            # Have to change "nrow" and "ncol" to "row" and "col"
            non = f
            if non[0] == 'n':
                non = non[1:]
            setattr(self, non, val)
        if obj is None and self.ind is not None:
            self.obj = objdata.ObjData()
            self.obj.get(dbcurs, ind=self.objind)
            self.istarget = self.obj.is_target()
            # Maybe adjust for PM? But we have RA/DEC as adjusted in structure

    def savedb(self, dbcurs):
        """Save record to database (provides for non-identified things)"""

        dbchanges = 0
        if self.ind is not None:
            dbchanges += dbcurs.execute("DELETE FROM aducalc WHERE frind={:d}".format(self.ind))
            dbchanges += dbcurs.execute("DELETE FROM findresult WHERE ind={:d}".format(self.ind))
        elif self.objind is not None and self.obsind is not None:
            dbchanges += dbcurs.execute("DELETE FROM aducalc WHERE objind={:d} AND obsind={:d}".format(self.objind, self.obsind))
            dbchanges += dbcurs.execute("DELETE FROM findresult WHERE objind={:d} AND obsind={:d}".format(self.objind, self.obsind))

        cols = []
        vals = []
        for field, typ in FindResult.frfields.items():
            if field[0] == 'n':
                val = getattr(self, field[:1], None)
            else:
                val = getattr(self, field, None)
            if val is None:
                continue
            # Give invalid code for things we don't want to save like ind
            try:
                vals.append(FindResult.frformats[typ].format(val))
            except KeyError:
                continue
            cols.append(field)

        dbchanges += dbcurs.execute("INSERT INTO findresult (" + ",".join(cols) + ") VALUES (" + ",".join(vals) + ")")
        self.ind = dbcurs.lastrowid
        if dbchanges > 0:
            dbcurs.connection.commit()


class FindResults:
    """A class for remembering things we've found"""

    # Fr_fields = dict(obsdate=xmlutil.getdatetime,
    #                  obsind=xmlutil.getint,
    #                  nrows=xmlutil.getint,
    #                  ncols=xmlutil.getint,
    #                  filter=xmlutil.gettext,
    #                  signif=xmlutil.getfloat,
    #                  totsignif=xmlutil.getfloat)

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

    def append_result(self, fr):
        """Append a result to result list. NB need to sort, relabel etc"""
        self.resultlist.append(fr)

    def insert_result(self, fr):
        """Append result if we haven't got it otherwise replace existing"""
        if fr.obj is not None:
            if fr.obj.objname in self.objdict:
                for n, r in enumerate(self.resultlist):
                    if r.obj is not None and r.obj.objind == fr.obj.objind:
                        self.resultlist[n] = fr
                        return
        self.resultlist.append(fr)

    def __getitem__(self, k):
        try:
            if isinstance(k, str):
                return  self.objdict[k]
            return self.resultlist[k]
        except (IndexError, KeyError):
            raise FindResultErr("Cannot find item " + str(k) + " in find results")

    def __setitem__(self, k, value):
        if isinstance(k, str):
            self.objdict[k] = value
        else:
            self.resultlist[k] = value

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

    def find_object(self, row, col, obj, searchp):
        """Fins specific object from expected place NB row and col might be fractional"""
        apsize = obj.apsize
        if apsize == 0:
            apsize = searchp.defapsize

        # This is the limit of the grid we look in
        lim = apsize + searchp.maxshift2
        ist = False
        if obj.is_target():
            ist = True
            lim = apsize + searchp.maxshift

        self.apsq = apsize**2
        scanlim = int(math.ceil(lim))
        scanpix = 2 * scanlim + 1
        scanrange = range(-scanlim, scanlim + 1)
        xpixes = np.tile(scanrange, (scanpix, 1))
        ypixes = xpixes.transpose()
        xypixes = [(y, x) for x, y in zip(xpixes.flatten(), ypixes.flatten()) if x**2 + y** 2 <= self.apsq]

        srow = int(round(row))
        scol = int(round(col))

        # Get segment of array, subtracting off sky level which we created previously

        dataseg = self.remfitsobj.data[srow-scanlim:srow+scanlim+1,scol-scanlim:scol+scanlim+1] - self.remfitsobj.skylev

        datavalues = np.array([dataseg[y + scanlim, x + scanlim] for y, x in xypixes])
        xypixes = np.array(xypixes)

        meanv = datavalues.mean()
        datavalues /= meanv

        try:
            lresult, lfiterrs = opt.curve_fit(gauss2d.gauss_circle, xypixes, datavalues, p0=(0.0, 0.0, max(datavalues), np.std(datavalues)))
        except RuntimeError:
            raise  FindResultErr("Unable to find {:s}".format(obj.dispname))

        fr = FindResult(obj=obj, apsize=apsize)
        cdiff, rdiff, fr.amp, fr.sigma = lresult
        dummy, dummy, fr.ampstd, fr.sigmastd = np.diag(lfiterrs)
        # cdiff += col - scol
        # rdiff += row - srow
        fr.amp *= meanv
        fr.ampstd *= meanv
        cdiff = col - scol - cdiff
        rdiff = row - srow - rdiff
        fr.col = col - cdiff
        fr.row = row - rdiff
        fr.cdiff = cdiff
        fr.rdiff = rdiff
        fr.radeg = obj.ra
        fr.decdeg = obj.dec
        fr.istarget = ist

        # Now calculate ADUs from data and from fit

        xypixes = [(x, y) for x, y in zip(xpixes.flatten(), ypixes.flatten()) if (x - fr.cdiff)**2 + (y - fr.rdiff) ** 2 <= self.apsq]
        # print("xypixes", xypixes, sys.stderr)
        # print("dataseg points", [dataseg[y+scanlim,x+scanlim] for x, y in xypixes], sys.stderr)
        fr.adus = np.sum([dataseg[y + scanlim, x + scanlim] for x, y in xypixes])
        fr.modadus = np.sum(gauss2d.gauss_circle(np.array(xypixes), fr.cdiff, fr.rdiff, fr.amp, fr.sigma))

        # plotfigure = plt.figure()
        # ax = plotfigure.add_subplot(111, projection='3d')
        # ax.plot_wireframe(xpixes, ypixes, dataseg, color='b', alpha=.5)
        # fitpoints = gauss2d.gauss2d(xpixes-fr.cdiff, ypixes-fr.rdiff, fr.amp, fr.sigma)
        # ax.plot_surface(xpixes, ypixes, fitpoints, color='g', alpha=.5)
        # plt.show()
        return  fr

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

    # def load(self, node):
    #     """Load up from XML dom"""
    #
    #     self.obsdate = None
    #     self.obsind = None
    #     self.nrows = self.ncols = None
    #     self.filter = None
    #     self.resultlist = []
    #     self.signif = None
    #     self.totsignif = None
    #
    #     for child in node:
    #         tagn = child.tag
    #         try:
    #             setattr(self, tagn, FindResults.Fr_fields[tagn](child))
    #         except KeyError:
    #             if tagn == "results":
    #                 for gc in child:
    #                     fr = FindResult()
    #                     fr.load(gc)
    #                     self.resultlist.append(fr)
    #     self.rekey()
    #
    # def save(self, doc, pnode, name):
    #     """Save to XML DOM node"""
    #     node = ET.SubElement(pnode, name)
    #     for k in FindResults.Fr_fields:
    #         v = getattr(self, k, None)
    #         if v is not None:
    #             xmlutil.savedata(doc, node, k, v)
    #     if len(self.resultlist) != 0:
    #         gc = ET.SubElement(node, "results")
    #         for fr in self.results():
    #             fr.save(doc, gc, "result")

    def adjust_offsets(self, dbcurs, rowdiff, coldiff):
        """Adjust row and column difference fields after we've adjusted that for obs"""
        donefr = 0
        for fr in self.resultlist:
            fr.rdiff += rowdiff
            fr.cdiff += coldiff
            if fr.ind is not None:
                donefr += dbcurs.execute("UPDATE findresult SET rdiff={:.4f},cdiff={:.4f} WHERE ind={:d}".format(fr.rdiff, fr.cdiff, fr.ind))
        return  donefr

    def loaddb(self, dbcurs):
        """Load from database note assumes remfitsobj filled in"""
        try:
            obsind = self.remfitsobj.from_obsind
        except  AttributeError:
            raise FindResultErr("loaddb called with no remfitsobj")

        self.resultlist = []

        dbcurs.execute("SELECT ind FROM findresult WHERE obsind={:d}".format(obsind))
        frres = dbcurs.fetchall()
        dbcurs.execute("SELECT filter,date_obs,nrows,ncols FROM obsinf WHERE obsind={:d}".format(obsind))
        obsinf = dbcurs.fetchone()
        if obsinf is None:
            raise FindResultErr("No obsinf for obsind={:d}".format(obsind))
        self.filter, self.obsdate, self.nrows, self.ncols = obsinf
        self.obsind = obsind

        for frrind, in frres:
            fr = FindResult()
            fr.loaddb(dbcurs, ind=frrind)
            fr.obj = objdata.ObjData()
            fr.obj.get(dbcurs, ind=fr.objind)
            self.resultlist.append(fr)

        self.reorder()
        self.relabel()
        self.rekey()

    def savedb(self, dbcurs, delete_previous = False):
        """Save records to database leaving along previously unsave records unless delete_previous set"""

        for fr in self.resultlist:
            if fr.ind is None or delete_previous:
                fr.savedb(dbcurs)
