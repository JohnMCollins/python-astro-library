import re
from astropy.time import Time
from astropy.io import fits
import io
import gzip

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
fmtch = re.compile('([FBIm]).*([UB][LR])')
ftypes = dict(F='Daily flat', B='Daily bias', I='Image', m='Master')


class RemFitsHdrErr(Exception):
    """Throw this is something wrong"""
    pass


class RemFitsHdr(object):
    """Get bits we want from header"""

    def __init__(self, hdr, nofn=False):

        global filtfn, fmtch, ftypes

        self.date = None
        self.filter = None
        self.ftype = None
        self.description = None
        self.startx = 0
        self.starty = 0
        self.endx = 1024
        self.endy = 1024
        self.ncolumns = 1024
        self.nrows = 1024

        for d in ('DATE-OBS', 'DATE', '_ATE'):
            try:
                self.date = Time(hdr[d]).datetime
            except KeyError:
                pass
        if self.date is None:
            raise RemFitsHdrErr("No date found in hheader")

        dfmtd = self.date.strftime("%d/%m/%Y @ %H:%M:%S")

        try:
            self.filter = hdr['FILTER']
        except KeyError:
            pass

        if nofn:
            if self.filter is None:
                raise RemFitsHdrErr("No filename and no filter given")
            self.ftype = "REMIR file"
            self.description = "REMIR file dated " + dfmtd
            try:
                self.endx = self.ncolumns = hdr['NAXIS1']
                self.endy = self.nrows = hdr['NAXIS2']
            except KeyError:
                raise("Dimensions of data not given in FITS header")
        else:
            try:
                ifname = hdr['FILENAME']
            except KeyError:
                raise RemFitsHdrErr("No internal filename in FITS header")

            mtches = fmtch.match(ifname)
            if mtches is None:
                if self.filter is None:
                    raise RemFitsHdrErr("No filter given and no decipherable filename")
                self.ftype = 'Processed image'
            else:
                ft, quad = mtches.groups()
                hfilt = filtfn[quad]
                try:
                    self.ftype = ftypes[ft]
                except KeyError:
                    self.ftype = 'Processed image'
                if self.filter is None:
                    self.filter = hfilt
                elif hfilt != self.filter:
                    raise RemFitsHdrErr("Conflig on filter types between " + self.filter + " and internal filename " + ifname + " suggesting " + hfilt)

            self.description = self.ftype + " dated " + dfmtd

            try:
                self.startx = hdr['startX']
                self.starty = hdr['startY']
                self.endx = hdr['endX']
                self.endy = hdr['endY']
                self.ncolumns = self.endx - self.startx
                self.nrows = self.endy - self.starty
            except KeyError as e:
                raise RemFitsHdrErr(e.args[0])

            if self.startx >= 1024:
                if self.filter not in 'gr':
                    raise RemFitsHdrErr("Filter " + self.filter + " not expected to be on right of CCD")
            else:
                if self.filter not in 'iz':
                    raise RemFitsHdrErr("Filter " + self.filter + " not expected to be on left of CCD")
            if self.starty >= 1024:
                if self.filter not in 'gi':
                    raise RemFitsHdrErr("Filter " + self.filter + " not expected to be on top of CCD")
            else:
                if self.filter not in 'rz':
                    raise RemFitsHdrErr("Filter " + self.filter + " not expected to be on bottom of CCD")


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
