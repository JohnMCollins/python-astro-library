# Operations on FITS files

"""Operations on FITS files"""

import gzip
import io
from astropy.io import fits


def mem_open(bytestring, compressed=True):
    """Open the given byte string as an in-memory FITS fite"""

    stream = bytestring
    if compressed:
        try:
            stream = gzip.decompress(bytestring)
        except OSError:
            return None
    try:
        return fits.open(io.BytesIO(stream), memmap=False, lazy_load_hdus=False)
    except OSError:
        return None


def mem_get(bytestring, compressed=True):
    """Return header, data from in memory FITS file assuming just 1 HDU"""
    ff = mem_open(bytestring, compressed)
    if ff is None:
        return (None, None)
    hdr = ff[0].header
    data = ff[0].data
    ff.close()
    return (hdr, data)


def mem_makefits(hdr, data, compressed=True):
    """Generate new FITS file in memory from header and date"""
    hdu = fits.PrimaryHDU(data, hdr)
    mm = io.BytesIO()
    hdu.writeto(mm)
    stream = mm.getvalue()
    bytestring = stream
    if compressed:
        bytestring = gzip.compress(stream)
    return bytestring
