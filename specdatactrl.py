# Spectral data control file

import numpy as np
import os.path
import glob
import string
import re
import xml.etree.ElementTree as ET
import datetime

import jdate
import xmlutil
import datarange
import doppler

SPC_DOC_NAME = "SPCCTRL"
SPC_DOC_ROOT = "spcctrl"
CFILEELEM = "cfile"

# Possible columns in observation times file

Obsfields = (('specfile', 'Spectrum filename'),
             ('jdate', 'Julian Date'),
             ('modjdate', 'Modified Julian Date'),
             ('bjdate', 'Barycentric Julian Date'),
             ('modbjdate', 'Modified Barycentric Date'),
             ('hvcorrect', 'Heliocentric Velocity Correction'),
             ('yerror', 'Y error for all of dataset'),
             ('ysnr', 'Signal to noise for all of dataset'))

# Possible columns in spectral data file

Specfields = (('xvalues', 'X (wavelength) values'),
              ('yvalues', 'Y (intensity) values'),
              ('yerr', 'Y errors individual point'),
              ('ignored', 'Ignored column'))

# This is the reference wavelength for working out the slope adjustment

Default_ref_wavelength = 6562.8
Filetimematch = re.compile('(\d\d\d\d)\D(\d\d)\D(\d\d)\D(\d\d)\D(\d\d)\D(\d\d)(\.\d+)?')

def jd_parse_from_filename(fn):
    """Parse filename to get jdate if possible"""

    mtch = Filetimematch.search(fn)
    if mtch is None:
        return None
    mtchl = list(mtch.groups())
    ms = mtchl.pop()
    mtchl = [ int(m) for m in mtchl ]
    if ms is None: ms = 0
    else: ms = int(round(float(ms), 6) * 1e6)
    mtchl.append(ms)
    return  jdate.datetime_to_jdate(datetime.datetime(*mtchl))

class SpecDataError(Exception):
    pass

class SpecDataArray(object):
    """This class holds a set of spectral data

       We use numpy arrays for both X and Y values after loading"""

    def __init__(self, filename, cols = ('xvalues', 'yvalues'), mjdate = 0.0, mbjdate = 0.0, hvc = 0.0):

        # Spectral data file name may possibly be absolute, but usually not
        self.filename = filename

        # Link back to containing array
        self.listlink = None

        # Names of columns used for spectral data
        self.cols = cols

        # "discount" is set true if we are ignoring this spectrum for any reason
        # "remarks" is a text string giving a reason for ignoring it or some other
        # comment if "discount" is not set

        self.discount = False
        self.remarks = None

        # Numpy arrays of xvalues, yvalues and y errors
        self.xvalues = None
        self.yvalues = None
        # yerr is a possible array of values
        # yerror is a single value for everything
        # with both yerr takes precedence
        # ysnr is alternative signal to noise
        self.yerr = None
        self.yerror = None
        self.ysnr = None

        # Mod Jdate and Mod Barycentric Jdate
        # It is a mistake not to have the latter set
        self.modjdate = mjdate
        self.modbjdate = mbjdate
        self.hvcorrect = hvc

        # Y scale is just a number possibly applied, default 1.0
        # Y offset is now a vector of coefficients of the polynomial for continuum fit
        # It may be empty in which case we use the global one.
        # We don't try to combine the two
        self.yscale = 1.0
        self.yoffset = None

        # These are for storing stuff when we're doing individual continuum calculations

        self.tmpxvals = None
        self.tmpyvals = None
        self.tmpcoeffs = None
        self.stddev = 0.0

    # Hash function uses mod barycentric date, mistake not to set it

    def __hash__(self):
        return str.__hash__("%.6f" % self.modbjdate)

    def tmpreset(self):
        """Fix temp space when iterating individual continua"""
        self.tmpcoeffs = None
        self.tmpxvals = None
        self.tmpyvals = None

    def loadfile(self, directory):
        """Load up spectral data from file

        Pass directory name and mod date"""

        # Ignore if done this already
        if self.xvalues is not None:
            return

        # Get full path name of file
        fname = self.filename
        if not os.path.isabs(fname):
            fname = os.path.join(directory, fname)
        try:
            mat = np.loadtxt(fname, unpack=True)
        except IOError as e:
            raise SpecDataError("Loading " + fname + " gave error: " + e.args[1])

        for cnum, field in enumerate(self.cols):
            try:
                setattr(self, field, mat[cnum])
            except IndexError:
                raise SpecDataError("No column " + str(cnum) + " (" + field + ") in data")

    def skip(self, reason, discount = True):
        """Set comment against data and mark whether to ignore it or not.

        Default is to do so"""
        self.discount = discount
        self.remarks = reason
        try:
            self.listlink.dirty = True
        except AttributeError as TypeError:
            pass

    def is_skipped(self):
        """Return reason for skipping data if applicable otherwise false"""
        if not self.discount:
            return False
        return self.remarks

    def get_xvalues(self, inclall = True):
        """Get X values after applying offset and scaling

        Argument gives whether we argue about skipped values (default no)
        File is assumed to be loaded."""

        if not inclall:
            sk = self.is_skipped()
            if sk:
                raise SpecDataError("Discounted data", self.filename, sk)

        res = self.xvalues
        if res is None:
            raise SpecDataError("Data for " + self.filename + " is not loaded")

        # Don't use += or similar below the first time or the whole array will be mangled
        # Apply scaling and offsets - change - now individual was cumulative.

        try:
            netcorrect = self.listlink.rvcorrect + self.hvcorrect / 1000.0

            if netcorrect != 0.0:
                res = doppler.vec_doppler(res, netcorrect)

        except AttributeError as TypeError:
            raise SpecDataError("Link error missing in " + self.filename)
        return res

    def apply_y_scale_offset(self, yvalues):
        """Apply Y scale and offset settings, used for both Y values and error values"""

        # Don't use += or similar below the first time or the whole array will be mangled
        # Apply scaling and offsets - change - now individual was cumulative.

        try:
            scale = self.listlink.yscale
            moffs = self.listlink.yoffset
        except (AttributeError, TypeError):
            raise SpecDataError("Link error missing in " + self.filename)

        scale *= self.yscale

        # NB apply offset before we apply scale

        if moffs is not None:
            yvalues = yvalues / np.polyval(moffs, self.get_xvalues(True) - self.listlink.refwavelength)
        if self.yoffset is not None:
            yvalues = yvalues / np.polyval(self.yoffset, self.get_xvalues(True) - self.listlink.refwavelength)
        if scale != 1.0:
            yvalues = yvalues * scale
        return yvalues

    def get_raw_yvalues(self):
        """Get unadjusted Y values for comparison with other ways of doing things"""
        res = self.yvalues
        if res is None:
            raise SpecDataError("Data for " + self.filename + " is not loaded")
        return  res

    def get_yvalues(self, inclall = True):
        """Get Y values after applying offset and scaling

        Argument gives whether we argue about skipped values (default no)
        File is assumed to be loaded."""

        if not inclall:
            sk = self.is_skipped()
            if sk:
                raise SpecDataError("Discounted data", self.filename, sk)

        res = self.yvalues
        if res is None:
            raise SpecDataError("Data for " + self.filename + " is not loaded")

        return self.apply_y_scale_offset(res)

    def get_yerrors(self, inclall = True, rawvals=False):
        """Get Y errors, either from "global" one from the entire spectrum, or from individual lines

        Argument gives whether we argue about skipped values (default no)
        File is assumed to be loaded."""

        if not inclall:
            sk = self.is_skipped()
            if sk:
                raise SpecDataError("Discounted data", self.filename, sk)
        if self.ysnr is not None:
            if rawvals:
                yvals = self.get_raw_yvalues()
            else:
                yvals = self.get_yvalues()
            return  np.zeros_like(yvals) + np.sqrt(np.mean(np.square(yvals))) / self.ysnr
        if self.yerr is None:
            if self.yvalues is None:
                raise SpecDataError("Data for " + self.filename + " is not loaded")
            res = np.zeros_like(self.yvalues)
            if self.yerror is None:
                return  res
            res += self.yerror
        else:
            res = self.yerr

        if rawvals:
            return res
        return self.apply_y_scale_offset(res)

    def getmaxminx(self, inclall = True):
        """Return tuple of mininmum and maximum x"""
        xvals = self.get_xvalues(inclall)
        return (min(xvals), max(xvals))

    def getmaxminy(self, inclall = True):
        """Return tuple of mininmum and maximum y"""
        yvals = self.get_yvalues(inclall)
        return (min(yvals), max(yvals))

    def load(self, node):
        """Load from XML DOM node"""
        self.filename = ""
        self.remarks = None
        self.discount = False
        self.xvalues = None
        self.yvalues = None
        self.yerr = None
        self.yerror = None
        self.ysnr = None
        self.modjdate = 0.0
        self.modbjdate = 0.0
        self.hvcorrect = 0.0
        self.yscale = 1.0
        self.yoffset = None

        for child in node:
            tagn = child.tag
            if tagn == "filename":
                self.filename = xmlutil.gettext(child)
            elif tagn == "discount":
                self.remarks = xmlutil.gettext(child)
                self.discount = not xmlutil.getboolattr(child, "nosupp")
            elif tagn == "modjdate":
                self.modjdate = xmlutil.getfloat(child)
            elif tagn == "modbjdate":
                self.modbjdate = xmlutil.getfloat(child)
            elif tagn == "yoffset":
                self.yoffset = xmlutil.getfloatlist(child)
            elif tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "hvcorrect":
                self.hvcorrect = xmlutil.getfloat(child)
            elif tagn == "yerror":
                self.yerror = xmlutil.getfloat(child)
            elif tagn == "ysnr":
                self.ysnr = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "filename", self.filename)
        if self.remarks is not None:
            ch = xmlutil.savedata(doc, node, "discount", self.remarks)
            xmlutil.setboolattr(node, "nosupp", not self.discount)
        if self.modjdate != 0.0:
            xmlutil.savedata(doc, node, "modjdate", self.modjdate)
        if self.modbjdate != 0.0:
            xmlutil.savedata(doc, node, "modbjdate", self.modbjdate)
        if self.yoffset is not None:
            xmlutil.savefloatlist(doc, node, "yoffset", self.yoffset)
        if self.yscale != 1.0:
            xmlutil.savedata(doc, node, "yscale", self.yscale)
        if self.hvcorrect != 0.0:
            xmlutil.savedata(doc, node, "hvcorrect", self.hvcorrect)
        if self.yerror is not None:
            xmlutil.savedata(doc, node, "yerror", self.yerror)
        if self.ysnr is not None:
            xmlutil.savedata(doc, node, "ysnr", self.ysnr)

def parse_jd(field):
    """Parse Julian date, checking it looks right"""
    if field[0:2] != "24":
        raise SpecDataError("Do not believe " + field + " is Julian date")
    # Don't convert the "24" to avoid rounding errors
    return  float(field[2:]) - 0.5

def parse_mjd(field):
    """Parse Modified Julian date, checking it looks right"""
    d = float(field)
    if d >= 2400000.0:
        raise SpecDataError("Do not believe " + field + " is Modified Julian date")
    return  d

class SpecDataList(object):
    """This class contains a list of spectral data"""

    #def __init__(self, obsfname = "", cols = ('specfile', 'modjdate', 'modbjdate', 'hvcorrect'), spdcols = ('xvalues','yvalues')):
    def __init__(self, obsfname = "", cols = ('modbjdate',), spdcols = ('xvalues','yvalues')):

        # If file name is given, initialise directory and observation files name
        # Do this because most of the time the obs file is in the same directory as
        # the spectra files.

        if len(obsfname) != 0:
            p = os.path.normpath(os.path.join(os.getcwd(), obsfname))
            if os.path.isfile(p):
                self.dirname, self.obsfname = os.path.split(p)
            elif os.path.isdir(p):
                self.dirname = p
                self.guessobsfile()
            else:
                raise SpecDataError("Cannot open obs dir/file " + p)
            self.objectname = os.path.basename(self.dirname)
        else:
            self.dirname = self.obsfname = self.objectname = ""

        # Set up reference wavelength for calculations of continuum curve
        # (We subtract this from the wavelength in question)
        self.refwavelength = Default_ref_wavelength

        # These are the names of columns in the obs file and the spectral data files
        self.cols = cols
        self.spdcols = spdcols

        self.resetall()

        # Set this to remember that we've made changes and need to save them
        self.dirty = False

        # These are set up and used in the parsing routines
        self.currentfile = ""
        self.modjdate = 0.0
        self.modbjdate = 0.0
        self.hvcorrect = 0.0
        self.yerror = None
        self.ysnr = None

    def is_complete(self):
        """Report whether file is complete"""
        return len(self.dirname) != 0 and len(self.obsfname) != 0 and len(self.datalist) != 0

    def resetall(self):
        """Reset all parameters after changing things"""

        # Radial velocity correction

        self.rvcorrect = 0.0

        # Y scale is such as to make the continuum mean (or possibly median) 1.0
        # Y offset is a vector of coefficients of the fitting polynomial for the continuum

        self.yscale = 1.0
        self.yoffset = None

        # This is the list of loaded data from the files.
        # We also remember the maximum and minimum X/Y values to save loading them each time

        self.datalist = []
        self.maxminx = None
        self.maxminy = None

    def set_dirname(self, dir):
        """Set the observation directory as given"""
        dir = os.path.abspath(dir)
        if not os.path.isdir(dir):
            raise SpecDataError("Invalid directory: " + dir)
        self.resetall()
        self.dirname = dir
        self.objectname = os.path.basename(self.dirname)
        self.guessobsfile()
        self.dirty = True

    def set_filename(self, file):
        """Set the observation file as given.
        Possibly reset the directory"""
        file = os.path.abspath(file)
        if not os.path.isfile(file):
            raise SpecDataError("Invalid file: " + file)
        dir, basefile = os.path.split(file)
        if dir == self.dirname and basefile == self.obsfname: return
        self.resetall()
        self.dirname = dir
        self.objectname = os.path.basename(self.dirname)
        self.obsfname = basefile
        self.dirty = True

    def classify_files(self):
        """Read file names in observations directory.
        Of the file names read return the prefix (we use first 5 chars)
        of the most common prefix file and the file name of any other file
        if there's only one"""

        filelist = glob.glob(self.dirname + '/*')
        occs = dict()
        for f5 in [os.path.basename(ff)[0:5] for ff in filelist]:
            try:
                occs[f5] = occs[f5] + 1
            except KeyError:
                occs[f5] = 1
        revoccs = dict()
        for k,v in list(occs.items()):
            revoccs[v] = k
        dprefix = revoccs[max(occs.values())]
        if len(occs) == 2 and min(occs.values()) == 1:
            fprefix = revoccs[1]
            oflist = glob.glob(self.dirname + '/' + fprefix + '*')
            return (dprefix, oflist[0])
        return (dprefix, "")

    def guessobsfile(self):
        """Try to figure out the name of the observation file having got the
        directory"""
        dprefix, obsf = self.classify_files()
        self.obsfname = obsf

    def getdatafilenames(self):
        """Get a sorted list of the data files"""
        dprefix, obsf = self.classify_files()
        filelist = glob.glob(self.dirname + '/' + dprefix + '*')
        filelist = [os.path.basename(x) for x in filelist]
        filelist.sort()
        return  filelist

    # The following routines are automatically invoked during the parsing
    #####################################################################

    def parse_jdate(self, field):
        """Parse julian date"""
        self.modjdate = parse_jd(field)

    def parse_mjdate(self, field):
        """Parse modified julian date"""
        self.modjdate = parse_mjd(field)

    def parse_bjdate(self, field):
        """Parse barycentric date"""
        self.modbjdate = parse_jd(field)

    def parse_mbjdate(self, field):
        """Parse modified barycentric date"""
        self.modbjdate = parse_mjd(field)

    def parse_hvcorrect(self, field):
        """Parse heliocentric vel correction"""
        self.hvcorrect = float(field)

    def parse_yerror(self, field):
        self.yerror = float(field)

    def parse_ysnr(self, field):
        self.ysnr = float(field)

    def parse_filename(self, field):
        """If file name is given, check it's the one we were expecting"""
        if field != self.currentfile:
            raise SpecDataError("File name out of sync read " + field + " expecting " + self.currentfile)

    # Lookup table for column name to routine

    routs = dict(specfile = parse_filename,
                 jdate = parse_jdate,
                 modjdate = parse_mjdate,
                 bjdate = parse_bjdate,
                 modbjdate = parse_mbjdate,
                 hvcorrect = parse_hvcorrect,
                 yerror = parse_yerror,
                 ysnr = parse_ysnr)

    # End of parsing routines
    #########################

    def loadfile(self):
        """Load observation file and set up data list"""

        fname = os.path.join(self.dirname, self.obsfname)
        try:
            fin = open(fname)
        except IOError as e:
            raise SpecDataError("Cannot open obs time file - " + e.args[0])

        filelist = self.getdatafilenames()
        nfiles = len(filelist)
        if nfiles < 1:
            raise SpecDataError("Unable to find any spectrum files")

        # No parse each file

        self.datalist = []
        reparser = re.compile("\s+")
        for line in fin:
            line = string.strip(line)
            if len(line) == 0: continue
            data = reparser.split(line)
            try:
                self.currentfile = filelist.pop(0)
            except IndexError:
                raise SpecDataError("Too few spectrum files " + str(nfiles) + " found to match observation file")
            self.modjdate = 0.0
            self.modbjdate = 0.0
            self.hvcorrect = 0.0
            self.yerror = None
            self.ysnr = None

            for n, c in enumerate(self.cols):
                try:
                    parserout = SpecDataList.routs[c]
                    parserout(self, data[n])
                except KeyError:
                    raise SpecDataError("Unknown column name " + c + " in SpecDataList")
                except IndexError:
                    raise SpecDataError("Column number " + str(n) + " out of range in SpecDataList")
                except ValueError as e:
                    raise SpecDataError("Conversion error in SpecDataList - " + e.args[0])

            # If we haven't got modjdate set, try to set it from the file name which HAPRS files include it in

            if self.modjdate == 0.0:
                jd = jd_parse_from_filename(self.currentfile)
                if jd is None:
                    self.modjdate = self.modbjdate
                else:
                    self.modjdate = jd

            newarray = SpecDataArray(self.currentfile, self.spdcols, self.modjdate, self.modbjdate, self.hvcorrect)
            if self.yerror is not None:
                newarray.yerror = self.yerror
            if self.ysnr is not None:
                newarray.ysnr = self.ysnr
            newarray.listlink = self
            self.datalist.append(newarray)
        if len(filelist) != 0:
            raise SpecDataError("Too many files found " + str(nfiles) + " found to match observation file " + str(len(filelist)) + " left over")
        fin.close()

    def loadfiles(self, flist = None):
        """Load all the files"""
        if flist is None: flist = self.datalist
        for f in flist:
            f.loadfile(self.dirname)

    def loadmaxmin(self):
        """Load up maxes and mins for other routines"""
        if self.maxminx is not None and self.maxminy is not None: return
        self.loadfiles()
        xvminmax = []
        yvminmax = []
        for f in self.datalist:
            try:
                xvminmax.append(f.getmaxminx(False))
                yvminmax.append(f.getmaxminy(False))
            except SpecDataError:
                pass
        if len(xvminmax) == 0:
            raise SpecDataError("Cannot find any X or Y values for max/min")
        self.maxminx = datarange.DataRange(min([v[0] for v in xvminmax]),max([v[1] for v in xvminmax]))
        self.maxminy = datarange.DataRange(min([v[0] for v in yvminmax]),max([v[1] for v in yvminmax]))
        self.dirty = True

    def getmaxmin(self):
        """Return ((minx,maxx),(miny,maxy))"""
        self.loadmaxmin()
        return (self.maxminx, self.maxminy)

    def getmaxminx(self):
        """Get just max and min for x as tuple"""
        self.loadmaxmin()
        return (self.maxminx.lower, self.maxminx.upper)

    def getmaxminy(self):
        """Get just max and min for y as tuple"""
        self.loadmaxmin()
        return (self.maxminy.lower, self.maxminy.upper)

    def count_indiv_x(self):
        """Count number of individual scales or offsets in X values"""
        return len([d for d in self.datalist if d.hvcorrect != 0.0])

    def count_indiv_y(self):
        """Count number of individual scales or offsets in Y values"""
        return len([d for d in self.datalist if d.yscale != 1.0 or d.yoffset is not None])

    def count_markers(self):
        """Count the number discounted"""
        return len([ d for d in self.datalist if d.discount ])

    def reset_markers(self):
        """Reset any discount markers, return number reset"""
        ndone = 0
        for d in self.datalist:
            if d.discount:
                d.discount = False
                d.remarks = 'Reset:' + d.remarks
                ndone += 1
        self.dirty = self.dirty or ndone > 0
        return ndone

    def clear_remarks(self):
        """Clear all traces of remarks on data"""
        ndone = 0
        for d in self.datalist:
            if d.discount or d.remarks is not None:
                d.discount = False
                d.remarks = None
                ndone += 1
        self.dirty = self.dirty or ndone > 0
        return ndone

    def tmpreset(self):
        """Clear temp markers"""
        for d in self.datalist: d.tmpreset()

    def copy_coeffs(self):
        """Copy coefficients of continuum calculations across"""
        for d in self.datalist:
            d.yoffset = d.tmpcoeffs
            d.tmpreset()
        self.dirty = True

    def reset_indiv_x(self):
        """Reset any individual hv corrections. Return whether we did anything"""
        if self.count_indiv_x() == 0:
            return False
        for d in self.datalist:
            d.hvcorrect = 0.0
        self.dirty = True
        return True

    def reset_x(self):
        """Reset the X rv correction. Return whether we did anything"""
        if self.rvcorrect == 0.0:
            return False
        self.rvcorrect = 0.0
        self.maxminx = None
        self.dirty = True
        return True

    def reset_indiv_y(self):
        """Reset any individual scales and offsets. Return whether we did anything"""
        if self.count_indiv_y() == 0:
            return False
        for d in self.datalist:
            d.yscale = 1.0
            d.yoffset = None
        self.dirty = True
        return True

    def reset_y(self):
        """Reset the Y scale and offset. Return whether we did anything"""
        if self.yscale == 1.0 and self.yoffset is None:
            return False
        self.yscale = 1.0
        self.yoffset = None
        self.maxminy = None
        self.dirty = True
        return True

    def set_rvcorrect(self, newrv):
        """Set new rv correction"""
        if self.rvcorrect == newrv:
            return
        self.rvcorrect = newrv
        self.minmax = None
        self.dirty = True

    def set_yscale(self, newsc):
        """Set y scale and adjust min/max if needed"""
        change = newsc / self.yscale
        if change == 1.0: return
        if self.maxminy is not None:
            self.maxminy = datarange.DataRange(self.maxminy.lower * change, self.maxminy.upper * change)
        self.yscale = newsc
        self.dirty = True

    def set_yoffset(self, newoff):
        """Set y offset and adjust min/max if needed"""
        if not np.iterable(newoff):
            raise SpecDataError("Y offsets must be iterable")
        self.yoffset = newoff
        self.maxminy = None
        self.dirty = True

    def set_refwavelength(self, val):
        """Adjust ref wavelength"""
        self.refwavelength = val
        self.dirty = True

    def load(self, node):
        """Load control file from XML file"""
        self.dirname = self.obsfname = self.objectname = ""
        self.cols = []
        self.spdcols = []
        self.yoffset = None
        self.yscale = 1.0
        self.rvcorrect = 0.0
        self.refwavelength = Default_ref_wavelength
        self.datalist = []
        self.maxminx = None
        self.maxminy = None
        self.dirty = False
        for child in node:
            tagn = child.tag
            if tagn == "dirname":
                self.dirname = xmlutil.gettext(child)
            elif tagn == "obsfname":
                self.obsfname = xmlutil.gettext(child)
            elif tagn == "objname":
                self.objectname = xmlutil.gettext(child)
            elif tagn == "obscols":
                for ochild in child: self.cols.append(xmlutil.gettext(ochild))
            elif tagn == "spcols":
                for schild in child: self.spdcols.append(xmlutil.gettext(schild))
            elif tagn == "rvcorrect":
                self.rvcorrect = xmlutil.getfloat(child)
            elif tagn == "yoffset":
                self.yoffset = xmlutil.getfloatlist(child)
            elif tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "refwavel":
                self.refwavelength = xmlutil.getfloat(child)
            elif tagn == "maxminx":
                self.maxminx = datarange.DataRange()
                self.maxminx.load(child)
            elif tagn == "maxminy":
                self.maxminy = datarange.DataRange()
                self.maxminy.load(child)
            elif tagn == "data":
                for dnode in child:
                    sa = SpecDataArray("")
                    sa.load(dnode)
                    sa.listlink = self
                    self.datalist.append(sa)
        if len(self.objectname) == 0 and len(self.dirname) != 0:
            self.objectname = os.path.basename(self.dirname)
        for d in self.datalist:     # Do this last in case data loaded first
            d.cols = self.spdcols

    def save(self, doc, pnode, name):
        """Save to XML file"""
        node = ET.SubElement(pnode, name)
        if len(self.dirname) != 0:
            xmlutil.savedata(doc, node, "dirname", self.dirname)
        if len(self.obsfname) != 0:
            xmlutil.savedata(doc, node, "obsfname", self.obsfname)
        if len(self.objectname) != 0:
            xmlutil.savedata(doc, node, "objname", self.objectname)
        colsnode = ET.SubElement(node, "obscols")
        for c in self.cols: xmlutil.savedata(doc, colsnode, "oc", c)
        colsnode = ET.SubElement(node, "spcols")
        for c in self.spdcols: xmlutil.savedata(doc, colsnode, "sc", c)
        if self.rvcorrect != 0.0: xmlutil.savedata(doc, node, "rvcorrect", self.rvcorrect)
        if self.yoffset is not None: xmlutil.savefloatlist(doc, node, "yoffset", self.yoffset)
        if self.yscale != 1.0: xmlutil.savedata(doc, node, "yscale", self.yscale)
        xmlutil.savedata(doc, node, "refwavel", self.refwavelength)
        if self.maxminx is not None: self.maxminx.save(doc, node, "maxminx")
        if self.maxminy is not None: self.maxminy.save(doc, node, "maxminy")
        dnode = ET.SubElement(node, "data")
        for d in self.datalist:
            d.save(doc, dnode, "array")
        self.dirty = False

def Load_specctrl(fname):
    """Load spectrum control file from given file"""
    try:
        doc, root = xmlutil.load_file(fname, SPC_DOC_ROOT)
        newlist = SpecDataList(fname)
        cnode = xmlutil.find_child(root, CFILEELEM)
        newlist.load(cnode)
    except xmlutil.XMLError as e:
        raise SpecDataError("Load control file XML error: " + e.args[0])
    return newlist

def Save_specctrl(fname, speclist):
    """Save spectrum control file to file"""
    try:
        doc, root = xmlutil.init_save(SPC_DOC_NAME, SPC_DOC_ROOT)
        speclist.save(doc, root, CFILEELEM)
        xmlutil.complete_save(fname, doc)
    except xmlutil.XMLError as e:
        raise SpecDataError("Save control file XML error: " + e.args[0])
