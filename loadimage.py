# Load image from file, applying flat and bias files

from astropy.io import fits
import numpy as np
import trimarrays


class LoadImErr(Exception):
    """Throw this when we have an error"""
    pass


def loadimage(imfile, flatfile, biasfile):
    """Load image from file, applying flat and bias files"""

    try:
        ff = fits.open(flatfile)
        fd = ff[0].data
        ff.close()
        bf = fits.open(biasfile)
        bd = bf[0].data
        bf.close()
        imf = fits.open(imfile)
        imd = imf[0].data
        imf.close()
    except OSError as e:
        raise LoadImErr("Could not open file", e.strerror)

    fd = fd.astype(np.float32)
    bd = bd.astype(np.float32)
    imd = imd.astype(np.float32)

    fd = trimarrays.trimzeros(trimarrays.trimnan(fd))
    imd, bd = trimarrays.trimto(fd, imd, bd)

    return ((imd - bd) * fd.mean()) / fd


def loadimagehdr(imfile, flatfile, biasfile):
    """Load image from file, applying flat and bias files
       andso return heardr of image file"""

    try:
        ff = fits.open(flatfile)
        fd = ff[0].data
        ff.close()
        bf = fits.open(biasfile)
        bd = bf[0].data
        bf.close()
        imf = fits.open(imfile)
        fhdr = imf[0].header
        imd = imf[0].data
        imf.close()
    except OSError as e:
        raise LoadImErr("Could not open file", e.filename, e.strerror)

    fd = fd.astype(np.float32)
    bd = bd.astype(np.float32)
    imd = imd.astype(np.float32)

    fd = trimarrays.trimzeros(trimarrays.trimnan(fd))
    imd, bd = trimarrays.trimto(fd, imd, bd)

    return (fhdr, ((imd - bd) * fd.mean()) / fd)
