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
import apoffsets
import find_overlaps

DEFAULT_SIGN = 1.5
DEFAULT_TOTSIGN = .75

class FindResultErr(Exception):
    """"Throw if error faound option to retry without looking for offset"""

    def __init__(self, msg, retrynooff=False):
        super().__init__(msg)
        self.retrynooff = retrynooff


class FindResult:
    """Class for remembering a single result"""

    frfields = dict(obsind='d', objind='d', ind='Z', nrow='f', ncol='f', rdiff='f', cdiff='f', xoffstd='f', yoffstd='f',
                    radeg='f', decdeg='f', amp='f', sigma='f', ampstd='f', sigmastd='f', apsize='f',
                    adus='f', modadus='f', hide='b')
    frformats = dict(d='{:d}', f="{:.16e}", b="{:d}")

    def __init__(self, obj = None, objind = None, obsind = None, apsize = 0.0, ind = None):
        self.col = self.row = None
        self.radeg = self.decdeg = self.rdiff = self.cdiff = self.xoffstd = self.yoffstd = 0.0
        self.amp = self.sigma = self.ampstd = self.sigmastd = self.adus = self.modadus = 0.0
        self.obj = None
        self.label = ""
        self.istarget = self.hide = False
        self.ind = ind
        self.obj = obj
        self.objind = objind
        self.obsind = obsind
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
            self.modadus = 0.0
        else:
            self.modadus = self.amp * 2.0 * np.pi * (1.0 - self.sigma**2 * math.exp((apsize/self.sigma)**2 / -2.0))
        return  self.modadus

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

        # Various combinations depending on whether we've got object specified etc

        if obj is None:
            obj = self.obj
        else:
            self.obj = obj
        if obj is None:
            if objind is None:
                objind = self.objind
            else:
                self.objind = objind
        else:
            self.objind = objind = obj.objind

        if obsind is None:
            obsind = self.obsind
        else:
            self.obsind = obsind

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
            self.obj.ra = self.radeg
            self.obj.dec = self.decdeg

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
                val = getattr(self, field[1:], None)
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
            # print(dbchanges, "DB changes")
            dbcurs.connection.commit()

    def makesave(self):
        """Create a values block for a block save"""
        return "({:d},{:d},{:d},{:.4f},{:.4f},{:.10e},{:.10e},{:.4f},{:.4f},{:.4f},{:.4f},{:.10e},{:.10e},{:.10e},{:.10e},{:.2f},{:.10e},{:.10e})" \
            .format(self.obsind, self.objind, self.hide, self.row, self.col,
                    self.radeg, self.decdeg, self.rdiff, self.cdiff, self.xoffstd, self.yoffstd,
                    self.amp, self.sigma, self.ampstd, self.sigmastd, self.apsize, self.adus, self.modadus)

    def update(self, dbcurs):
        """Update details"""

        fields = []

        for field, typ in FindResult.frfields.items():
            if field[0] == 'n':
                val = getattr(self, field[1:], None)
            else:
                val = getattr(self, field, None)
            if val is None:
                continue
            # Give invalid code for things we don't want to save like ind
            try:
                fields.append("{:s}={:s}".format(field, FindResult.frformats[typ].format(val)))
            except KeyError:
                continue
        if len(fields) == 0:
            return 0
        return  dbcurs.execute("UPDATE findresult SET " + ",".join(fields) + " WHERE ind={:d}".format(self.ind))


    def delete(self, dbcurs):
        """Delete a find result and associated aducalcs"""
        if  self.ind is None:
            return
        dbchanges = dbcurs.execute("DELETE from aducalc WHERE frind={:d}".format(self.ind))
        dbchanges += dbcurs.execute("DELETE from findresult WHERE ind={:d}".format(self.ind))
        if  dbchanges > 0:
            dbcurs.connection.commit()
        self.ind = None

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
        self.objinddict = dict()
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

    def get_by_objind(self, objind):
        """Get findresult by object index"""
        try:
            return  self.objinddict[objind]
        except  KeyError:
            return  None

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
        self.objinddict = dict()
        for r in self.results():
            if r.obj is not None:
                self.objdict[r.obj.objname] = r
                self.objinddict[r.obj.objind] = r
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
        self.imagedata = self.remfitsobj.data - self.remfitsobj.skylev
        self.pixrows, self.pixcols = self.imagedata.shape

        self.currentap = apsize
        self.currentiap = int(math.floor(apsize))
        self.apsq = apsize ** 2
        self.minrow = self.mincol = self.currentiap + 1
        self.maxrow = self.pixrows - self.currentiap  # This is actually 1 more
        self.maxcol = self.pixcols - self.currentiap  # This is actually 1 more

        self.min_singlepix = self.remfitsobj.meanval + self.signif * self.remfitsobj.stdval

    def prune_singlepix(self, searchp, dseg, yxcoords):
        """Prune case where minimum level of pixels around a given pixel"""

        newresult = []
        drows, dcols = dseg.shape

        for y, x in yxcoords:
            if y <= 0 or y >= drows or x <= 0 or x >= dcols:
                continue
            if np.count_nonzero(dseg[y-1:y+1,x-1:x+1] >= self.min_singlepix) >= searchp.min_singlepix:
                newresult.append((y,x))
        return  newresult

    def get_aperture_data(self, row, column):
        """Get data in aperture according to mask"""
        halfside = self.currentiap + 1
        return  self.imagedata[row - self.currentiap:row + halfside, column - self.currentiap:column + halfside].flatten()[self.maskbool]

    def calculate_adus(self, row, column):
        """Calculate the total ADUs based arount the given row and column"""
        return  np.sum(self.get_aperture_data(row, column)) - self.skylevpoints

    def find_object(self, row, col, obj, searchp):
        """Fins specific object from expected place NB row and col might be fractional"""
        apsize = obj.apsize
        if apsize == 0:
            apsize = searchp.defapsize
        self.signif = searchp.signif
        self.get_image_dims(apsize)

        # This is the limit of the grid we look in
        lim = apsize + searchp.maxshift2
        ist = False
        if obj.is_target():
            ist = True
            lim = apsize + searchp.maxshift

        colfrac, scol = math.modf(col)
        rowfrac, srow = math.modf(row)
        scol = int(scol)
        srow = int(srow)
        xypixoffsets = apoffsets.ap_offsets(col, row, apsize)
        xypixes = xypixoffsets + (scol, srow)
        # print("xypixes shape", xypixes.shape, "val", xypixes)
        xpixes = xypixes[:,0]
        ypixes = xypixes[:,1]
        if xpixes.min() < self.mincol:
            raise FindResultErr("Cannot find {:s}, too close to left edge".format(obj.dispname))
        if xpixes.max() >= self.maxcol:
            raise FindResultErr("Cannot find {:s}, too close to right edge".format(obj.dispname))
        if ypixes.min() < self.minrow:
            raise FindResultErr("Cannot find {:s}, too close to bottom edge".format(obj.dispname))
        if ypixes.max() >= self.maxrow:
            raise FindResultErr("Cannot find {:s}, too close to top edge".format(obj.dispname))

        datavals = np.array([self.imagedata[y, x] for x, y in xypixes]) # NB Sky level subtracted

        # Normalise data values to 1 as fitting works better that way

        meanv = datavals.mean()
        ndatavals = datavals / meanv

        # print("Pixoffsets", xypixoffsets, "scol/srow", scol, srow, "col/rowfrac", colfrac, rowfrac)
        try:
            lresult, lfiterrs = opt.curve_fit(gauss2d.gauss_circle, xypixoffsets, ndatavals, p0=(colfrac, rowfrac, ndatavals.max(), np.std(ndatavals)))
        except (TypeError, RuntimeError):
            raise  FindResultErr("Unable to find {:s}".format(obj.dispname))

        fr = FindResult(obj=obj, apsize=apsize)
        cdiff, rdiff, fr.amp, fr.sigma = lresult
        # print("After fit cdiff={:.4f} rdiff={:.4f} amp={:.4f} sigma={:.4f}".format(*lresult))
        fr.xoffstd, fr.yoffstd, fr.ampstd, fr.sigmastd = np.diag(lfiterrs)
        if fr.xoffstd > searchp.offsetsig or fr.yoffstd > searchp.offsetsig:
            raise FindResultErr("Too great an offset error finding {:s} x={:.4g} y={:.4g}".format(obj.dispname, fr.xoffstd, fr.yoffstd), True)

        # Restore from normalisation

        fr.amp *= meanv
        fr.ampstd *= meanv

        if fr.amp <= 0.0 or fr.ampstd <= 0 or fr.amp < fr.ampstd * searchp.ampsig or fr.sigma < fr.sigmastd * searchp.sigmasig:
            raise FindResultErr("Unable to find {:s} - too much error stderr amp {:.4g} sigma {:.4g}".format(obj.dispname, fr.ampstd, fr.sigmastd))

        # The returned values of cdiff and rdiff are offsets from scol and srow
        # Set cdiff and rdiff in structure to where we expected them to be minus where they are

        fr.col = scol + cdiff
        fr.row = srow + rdiff
        fr.cdiff = col - fr.col
        fr.rdiff = row - fr.row
        fr.radeg = obj.ra
        fr.decdeg = obj.dec
        fr.istarget = ist

        if abs(fr.cdiff) > lim or abs(fr.rdiff) >= lim:
            raise FindResultErr("Unable to find {:s} - too much shift cdiff={:.2f} rdiff={:.2f}".format(obj.dispname, fr.cdiff, fr.rdiff))

        # Now calculate ADUs from data and from fit

        fr.adus = np.sum(datavals)
        fr.calculate_mod_integral()
        return  fr

    def find_peak(self, row, col, possobj, searchp):
        """Find peak for when we are giving a label to an object"""
        if possobj.apsize == 0:
            possobj.apsize = searchp.defapsize

        self.get_image_dims(possobj.apsize)
        self.min_singlepix = self.remfitsobj.meanval + searchp.signif * self.remfitsobj.stdval
        startrow = int(math.floor(max(row - searchp.maxshift, self.minrow)))
        startcol = int(math.floor(max(col - searchp.maxshift, self.mincol)))
        endrow = int(math.ceil(min(row + searchp.maxshift, self.maxrow)))
        endcol = int(math.ceil(min(col + searchp.maxshift, self.mincol)))
        numcols = endcol - startcol

        dataseg = self.imagedata[startrow:endrow, startcol:endcol]
        fimage = dataseg.flatten()
        order = fimage.argsort()[::-10]
        vals = fimage[order]
        signifs = order[vals >= self.min_singlepix]
        if len(signifs) == 0:
            return  None

        # Comvert to list of row,col coords
        yxvals = [(v // numcols, v % numcols) for v in signifs]

        # Prune single pixels out

        yxvals = self.prune_singlepix(searchp, dataseg, yxvals)
        if len(yxvals) == 0:
            return  None
        yxvals = find_overlaps.find_overlaps(yxvals, possobj.apsize) + (startcol, startrow)
        fitresults = []

        for y, x in yxvals:
            try:
                fr = self.find_object(y, x, possobj, searchp)
            except FindResultErr:
                continue

            fr.radeg, fr.decdeg = self.remfitsobj.wcs.colrow_to_coords(fr.col, fr.row)
            fitresults.append(fr)

        if len(fitresults) == 0:
            return  None

        if len(fitresults) != 1:
            fitresults = sorted(fitresults, key=lambda f: f.ampstd)
            fitresults = sorted(fitresults, key=lambda f: f.rdiff**2 + f.cdiff**2 - self.apsq)
        return  fitresults[0]

    def opt_aperture_list(self, row, col, searchp, minap=None, maxap=None, step=None):
        """Optimise aparture for given row and column."""

        if minap is None:
            minap = searchp.minap
        if maxap is None:
            maxap = searchp.maxap
        if step is None:
            step = searchp.apstep

        self.signif = searchp.signif
        self.get_image_dims(minap)

        if  row - maxap <= 0 or row + maxap + 1 >= self.pixrows or col - maxap <= 0 or col + maxap + 1 >= self.pixcols:
            raise  FindResultErr("Cannot optimise too close to edge")

        srow = int(row)
        scol = int(col)

        results = []

        for possap in np.arange(minap, maxap + step, step):
            xycoords = apoffsets.ap_offsets(col, row, possap)
            #print("xycoords", xycoords, "possap", possap)
            datavals = np.array([self.imagedata[y,x] for x,y in xycoords+(scol,srow)])
            #print("datavals", datavals)
            # Can't do curve fit with less than 4 points.
            if datavals.size <= 4:
                continue
            meanv = datavals.mean()
            datavals /= meanv
            try:
                lresult, lfiterrs = opt.curve_fit(gauss2d.gauss_circle, xycoords, datavals, p0=(col-scol, row-srow, max(datavals), np.std(datavals)))
            except (TypeError, RuntimeError):
                continue
            fr = FindResult(apsize=possap)
            cdiff, rdiff, fr.amp, fr.sigma = lresult
            fr.xoffstd, fr.yoffstd, fr.ampstd, fr.sigmastd = np.diag(lfiterrs)
            fr.amp *= meanv
            fr.ampstd *= meanv
            fr.col = scol + cdiff
            fr.row = srow + rdiff
            fr.cdiff = col - fr.col
            fr.rdiff = row - fr.row
            fr.adus = meanv

            # If offset is too much, skip or offset stds too much also skip

            if abs(cdiff) >= searchp.maxshift  or  abs(rdiff) >= searchp.maxshift:
                # print("Too big cdeff {:.4f} redif {:.4f} apsize {:.2f}".format(cdiff, rdiff, possap))
                continue
            if fr.xoffstd > searchp.offsetsig or fr.yoffstd > searchp.offsetsig:
                # print("Too big offstds {:.4f} {:.4f}".format(xoffstd, yoffstd))
                continue

            results.append(fr)

        if len(results) == 0:
            raise  FindResultErr("Cannot optimise object by Gauss fit")

        return  results

    def opt_aperture(self, row, col, searchp, minap=None, maxap=None, step=None):
        """Just give best aperture size"""

        results = self.opt_aperture_list(row, col, searchp, minap, maxap, step)
        means = []
        ampstds = []
        sigmastds = []
        for fr in results:
            means.append(fr.adus)
            ampstds.append(fr.ampstd)
            sigmastds.append(fr.sigmastd)

        means = np.array(means)
        ampstds = np.array(ampstds)
        sigmastds = np.array(sigmastds)

        means /= means.mean()
        ampstds /= ampstds.mean()
        sigmastds /= sigmastds.mean()

        combs = np.abs(means-ampstds) + np.abs(means-sigmastds) + np.abs(ampstds-sigmastds)
        ast = combs.argsort(kind='stable')
        return  results[ast[0]].apsize

        # results = sorted(sorted(results, key=lambda x: x[-1]/x[-3]), key=lambda x: x[-2]/x[-4])
        # results = sorted(results, key=lambda x: x[-1]/x[-3])

        # for possap, audpn, amp, sigma, ampstd, sigmastd in results:
        #    print("{:7.2f} {:10.2f} {:12.3f} {:12.3f} {:12.3f} {:12.3f} {:.4f} {:.4f}".format(possap, -audpn, amp, sigma, ampstd, sigmastd, ampstd/amp, sigmastd/sigma))
        # return  results

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

    def save_as_block(self, dbcurs, blocksize = 512):
        """Save records as single blocks"""
        fields = "(obsind,objind,hide,nrow,ncol,radeg,decdeg,rdiff,cdiff,xoffstd,yoffstd,amp,sigma,ampstd,sigmastd,apsize,adus,modadus) " \
        "VALUES "
        varr = []
        for fr in self.resultlist:
            varr.append(fr.makesave())
            if len(varr) >= blocksize:
                dbcurs.execute("INSERT INTO findresult " + fields + ",".join(varr))
                varr = []
        if len(varr) != 0:
            dbcurs.execute("INSERT INTO findresult " + fields + ",".join(varr))
        dbcurs.connection.commit()
