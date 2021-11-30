"""Classes for handling REM FITS files"""

import re
from astropy.time import Time
from astropy.io import fits
import numpy as np
import remget
import fitsops
import wcscoord
import miscutils

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
revfn = dict()
for k, v in filtfn.items():
    revfn[v] = k
fmtch = re.compile('([FBImCR]).*([UB][LR])')

# Second element tells us whether to look for coords
ftypes = dict(F=('Daily flat', False), B=('Daily bias', False), I=('Image', True), m=('Master', False), C=('Combined bias', False), G=('Generated flat', False))

remir_types = frozenset(['H', 'J', 'K', 'GRI'])


class RemFitsErr(Exception):
    """Throw this is something wrong"""


def check_has_dims(hdr):
    """Check that dimensions are set in header and return True"""
    try:
        return  (hdr['startX'], hdr['startY'])
    except KeyError:
        return  False


def set_dims_in_hdr(hdr, startx, starty, cols, rows):
    """Set up dimensions in header in one place so we can easily change it"""
    hdr['startX'] = (startx, 'Starting CCD pixel column')
    hdr['endX'] = (startx + cols, 'Ending CCD pixel column+1')
    hdr['startY'] = (starty, 'Starting CCD pixel row')
    hdr['endY'] = (starty + rows, 'Ending CCD pixel row+1')


class RemFitsHdr:
    """Get bits we want from header"""

    def __init__(self, hdr=None, nofn=False):

        self.hdr = None
        self.date = None
        self.target = None
        self.ccdtemp = None
        self.filter = None
        self.ftype = None
        self.description = None
        self.startx = 0
        self.starty = 0
        self.endx = 1024
        self.endy = 1024
        self.ncolumns = 1024
        self.nrows = 1024
        self.wcs = None
        if hdr is not None:
            self.init_from_header(hdr, nofn)

    def dims(self):
        """Quickly return dimensions as tuple"""
        return (self.startx, self.starty, self.endx, self.endy)

    def dimscr(self):
        """Quickly return dimensions as tuple with columns and rows for quick compare"""
        return (self.startx, self.starty, self.endx - self.startx, self.endy - self.starty)

    def init_from_header(self, hdr, nofn=False):
        """Initialise fields from header"""

        global filtfn, fmtch, ftypes

        self.hdr = hdr
        getwcs = False

        try:
            self.target = hdr['OBJECT']
        except KeyError:
            pass

        for d in ('DATE-OBS', 'DATE', '_ATE'):
            try:
                self.date = Time(hdr[d]).datetime
                break
            except KeyError:
                pass
        if self.date is None:
            raise RemFitsErr("No date found in hheader")

        for t in ('CCDTEMP', 'TEMPCHIP'):
            try:
                self.ccdtemp = hdr[t]
                break
            except KeyError:
                pass
        if self.ccdtemp is None:
            raise RemFitsErr("No temperature found in hheader")

        dfmtd = self.date.strftime("%d/%m/%Y @ %H:%M:%S")

        try:
            self.filter = hdr['FILTER']
        except KeyError:
            pass

        if nofn:
            if self.filter is None:
                raise RemFitsErr("No filename and no filter given")
            self.ftype = "REMIR file"
            getwcs = True
            self.description = "REMIR file dated " + dfmtd
            try:
                self.endx = self.ncolumns = hdr['NAXIS1']
                self.endy = self.nrows = hdr['NAXIS2']
            except KeyError:
                raise RemFitsErr("Dimensions of data not given in FITS header")
        elif self.filter in remir_types:
            self.description = "REMIR Image file dated " + dfmtd
            self.ftype = 'Image'
            self.startx = self.starty = 0
            self.endx = self.endy = 512
            getwcs = True
        else:
            try:
                ifname = hdr['FILENAME']
            except KeyError:
                raise RemFitsErr("No internal filename in FITS header")

            mtches = fmtch.match(ifname)
            if mtches is None:
                if self.filter is None:
                    raise RemFitsErr("No filter given and no decipherable filename")
                try:
                    self.ftype = ftypes[ifname[0]][0]
                except KeyError:
                    self.ftype = 'Processed image'
                getwcs = True
            else:
                ft, quad = mtches.groups()
                hfilt = filtfn[quad]
                try:
                    self.ftype, getwcs = ftypes[ft]
                except KeyError:
                    self.ftype = 'Processed image'
                    getwcs = True
                if self.filter is None:
                    self.filter = hfilt
                elif hfilt != self.filter:
                    raise RemFitsErr("Conflig on filter types between " + self.filter + " and internal filename " + ifname + " suggesting " + hfilt)

            self.description = self.ftype + " dated " + dfmtd

            try:
                self.startx = hdr['startX']
                self.starty = hdr['startY']
                self.endx = hdr['endX']
                self.endy = hdr['endY']
                self.ncolumns = self.endx - self.startx
                self.nrows = self.endy - self.starty
            except KeyError as e:
                raise RemFitsErr(e.args[0])

            if self.startx >= 1024:
                if self.filter not in 'gr':
                    raise RemFitsErr("Filter " + self.filter + " not expected to be on right of CCD")
            else:
                if self.filter not in 'iz':
                    raise RemFitsErr("Filter " + self.filter + " not expected to be on left of CCD")
            if self.starty >= 1024:
                if self.filter not in 'gi':
                    raise RemFitsErr("Filter " + self.filter + " not expected to be on top of CCD")
            else:
                if self.filter not in 'rz':
                    raise RemFitsErr("Filter " + self.filter + " not expected to be on bottom of CCD")

        if getwcs:
            self.wcs = wcscoord.wcscoord(hdr)


class RemFits(RemFitsHdr):
    """As above but hold data as well with appropriate trim and conversion"""

    def __init__(self, hdr=None, data=None, nofn=False, from_obsind=0):

        super().__init__(hdr, nofn)
        self.data = data
        self.meanval = 0.0
        self.stdval = 0.0
        if data is not None:
            self.norm_data()
        self.from_obsind = from_obsind

    def init_from_data(self, data):
        """Initialise from data given"""
        self.data = data
        self.norm_data()

    def init_from(self, hdr, data, nofn=False):
        """Initialise both"""
        self.init_from_header(hdr, nofn)
        self.init_from_data(data)

    def norm_data(self):
        """Set data to standard format"""
        if (self.nrows, self.ncolumns) < self.data.shape:
            self.data = self.data[0:self.nrows, 0:self.ncolumns]
        if self.data.dtype != np.float32:
            self.data = self.data.astype(np.float32)
        self.meanval = self.data.mean()
        self.stdval = self.data.std()

    def load_from_fits(self, fname):
        """Load and fill up from specified file"""
        try:
            ff = fits.open(miscutils.addsuffix(fname, 'fits.gz'))
        except OSError as e:
            if e.strerror is None:
                raise RemFitsErr(fname + " is not a valid FITS file")
            raise RemFitsErr("Open of " + fname + " (" + e.filename + ") gave error " + e.strerror)
        self.init_from(ff[0].header, ff[0].data)
        ff.close()

    def load_from_obsind(self, dbcurs, obsind):
        """Load and fill up from obsind"""
        try:
            ffmem = remget.get_obs_fits(dbcurs, obsind)
        except remget.RemGetError as e:
            raise RemFitsErr(e.args[0])
        hdr, data = fitsops.mem_get(ffmem)
        if hdr is None or data is None:
            raise RemFitsErr("Could not fetch obsind=$d" % obsind)
        self.init_from(hdr, data)
        self.from_obsind = obsind

    def load_from_iforbind(self, dbcurs, iforbind):
        """Load and fill up from iforbind"""
        try:
            ffmem = remget.get_iforb_fits(dbcurs, iforbind)
        except remget.RemGetError as e:
            raise RemFitsErr(e.args[0])
        hdr, data = fitsops.mem_get(ffmem)
        if hdr is None or data is None:
            raise RemFitsErr("Could not fetch iforbind=$d" % iforbind)
        self.init_from(hdr, data)

# Parse argument file and return a suitable RemFits object


def parse_filearg(name, dbcurs, typef=None):
    """Parse a file or ID string given. Should be of given type or don't care
    May expand this later to load up library files.
    Currently name is a file name if it isn't numeric, in which case it's supposed to be
    a FITS file.
    If it numeric, load from given obsid if type is None or from flat or bias file id if
    type is 'F' or 'B' or a saved FITS file if 'Z'
    If Flat or Bias file, check loaded file is correct type.
    We may extend this later to cope with expenaded Flat or Bias files."""

    fobs = 0

    if isinstance(name, int):
        try:
            if typef is None or typef == 'I':
                ffmem = remget.get_obs_fits(dbcurs, name)
                fobs = name
            elif typef == 'Z':
                ffmem = remget.get_saved_fits(dbcurs, name)
            else:
                ffmem = remget.get_iforb_fits(dbcurs, name)

            hdr, data = fitsops.mem_get(ffmem)

            if hdr is None:
                raise RemFitsErr("Could not decode FITS file for " + str(name))
            return  RemFits(hdr, data, from_obsind=fobs)

        except remget.RemGetError as e:
            raise RemFitsErr("Error fetching file for " + name + " - " + e.args[0])

    rname = name
    try:
        if name[1] == ':':
            typef = name[0]
            rname = name[2:]
    except IndexError:
        pass
    try:
        if rname.isnumeric():
            ind = int(rname)
            if typef is None or typef == 'I':
                ffmem = remget.get_obs_fits(dbcurs, ind)
                fobs = ind
            elif typef == 'Z':
                ffmem = remget.get_saved_fits(dbcurs, ind)
            else:
                ffmem = remget.get_iforb_fits(dbcurs, ind)

            hdr, data = fitsops.mem_get(ffmem)

            if hdr is None:
                raise RemFitsErr("Could not decode FITS file for " + name)
            return  RemFits(hdr, data, from_obsind=fobs)

        r = RemFits()
        r.load_from_fits(rname)

        if typef is not None and typef != 'Z':
            if typef == 'F' and r.ftype != 'Daily flat' and r.ftype != 'Combined flat' and r.ftype != 'Master':
                raise RemFitsErr("Expecting " + name + " to be flat file not " + r.ftype)
            if typef == 'B' and r.ftype != 'Daily bias' and r.ftype != 'Combined bias' and r.ftype != 'Master':
                raise RemFitsErr("Expecting " + name + " to be bias file not " + r.ftype)

        return  r

    except remget.RemGetError as e:
        raise RemFitsErr("Error fetching file for " + name + " - " + e.args[0])
