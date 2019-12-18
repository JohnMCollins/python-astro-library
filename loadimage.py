# Load image from file, applying flat and bias files

from astropy.io import fits
import numpy as np
import trimarrays

def loadimage(imfile, flatfile, biasfile):
    """Load image from file, applying flat and bias files"""
    
    ff = fits.open(flatfile)
    fd = ff[0].data
    ff.close()
    bf = fits.open(biasfile)
    bd = bf[0].data
    bf.close()
    imf = fits.open(imfile)
    imd = imf[0].data
    imf.close()
    
    fd = fd.astype(np.float32)
    bd = bd.astype(np.float32)
    imd = imd.astype(np.float32)
    
    fd = trimarrays.trimzeros(trimarrays.trimnan(fd))
    imd, bd = trimarrays.trimto(fd, imd, bd)
    
    return ((imd - bd) * fd.mean()) / fd
    