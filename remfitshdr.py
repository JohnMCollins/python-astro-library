import re
from astropy.time import Time

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
fmtch = re.compile('([FBIm]).*([UB][LR])')
ftypes = dict(F='Daily flat', B='Daily bias', I='Image', m='Master')


class RemFitsHdrErr(Exception):
    """Throw this is something wrong"""
    pass


class RemFitsHdr(object):
    """Get bits we want from header"""

    def __init__(self, hdr):

        global filtfn, fmtch, ftypes

        self.date = None
        self.filter = None
        self.ftype = None
        self.description = None

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
