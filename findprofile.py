# Try to identify profiles in spectra, returning either the maximum peak or the maximum peak and two minima

import numpy as np
import scipy.signal as ss

ERR_OK = 0
ERR_ZEROAMPS = 1
ERR_NOMAXES = 2
ERR_NOSIGMAXES = 3
ERR_EXCESSMAXES = 4
ERR_EXCESSMINS = 5
ERR_TOOFEWPTS = 6

Messages = ('OK',
            'Found -ve or zero amps',
            'Could not find any maxima'
            'Could not find significant maxima',
            'More than 2 maxima, cannot currently understand',
            'Only one maximum but > 0 minima',
            'Not enough points between maxima to find minimum')

class FindProfileError(Exception):
    """Class for returning errors in profile finding.
    
    We take a code which also corresponds to the message as defined above"""
    
    def __init__(self, code):
        global Messages
        super(FindProfileError, self).__init__(Messages[code])
        self.code = code

class Specprofile(object):
    """Class for representing type of spectral line"""
    
    def __init__(self, degfit = 20):
        
        self.twinpeaks = False              # Has twin-peaked "horn" format
        self.wavelengths = None             # A numpy array
        self.amplitudes = None              # Likewise (should be same length as wavelengths)
        self.maxima = None                  # List of indices into above for maxima
        self.minima = None                  # Ditto for minima
        self.ewinds = None                  # Indices we use for EW
        self.valid = False                  # Result currently valid
        self.passnum = 0                    # Pass number evaluated on
        self.degfit = degfit                # Degree of polynomial fit
        
    def setresult(self, maxima, minima, intthresh):
        """Calculate EW indices from intthresh and set result maxima and minima"""
        
        self.maxima = maxima
        self.minima = minima
        
        self.twinpeaks = len(maxima) == 2
        lhmax = maxima[0]
        rhmax = maxima[-1]
        ithr = intthresh + 1.0
        
        bthresh = np.argwhere(self.amplitudes < ithr).flatten()
        leftinds = bthresh[bthresh < lhmax]
        rightinds = bthresh[bthresh > rhmax]
        try:           
            leftew = leftinds[-1]+1
        except IndexError:
            leftew = 0
        try:
            rightew = rightinds[0]-1
        except IndexError:
            rightew = len(self.amplitudes)-1
        self.ewinds = (leftew, rightew)
        return  True
        
    def calcprofile(self, wavelengths, amps, central = 6563.0, sigthreash = 0.5, intthresh = 0.1):
        """Calculate the profile shape.
        
        Supply wavelengths and amplitudes
        central = central wavelenght (estimated) default 6563.0
        sigthresh = ignore maxima and minima with amplitudes less than this amount of minimum
        intthresh = intensity on edge of peak for selecting EW"""
        
        self.wavelengths = wavelengths
        self.amplitudes = amps
        
        # Work from either side of central wavelength it makes the numbers more manageable
        # Get min and max amplitude
        
        offset_wls = wavelengths - central
        minamp = np.min(amps)
        maxamp = np.max(amps)
        
        # Get indices of maxima and minima
        
        specmax = ss.argrelmax(amps)[0]
        specmin = ss.argrelmin(amps)[0]
        
        # If no maxima at all, we can't currently identify it
        # (assume we're working with emission lines right now)
        
        self.passnum = 1
        
        if len(specmax) == 0:
            raise FindProfileError(ERR_NOMAXES)
        
        # If one maximum and no minimum just assume a single peak
        # or if two maximum and one minimum we don't have to try too hard
        
        print "Specmax =", specmax, "Specmin =", specmin
        if len(specmax) == 1:
            if len(specmin) == 0:
                return  self.setresult(specmax, specmin, intthresh)
        elif len(specmax) == 2:
            if len(specmin) == 1 and specmax[0] < specmin[0] < specmax[1]:
                return  self.setresult(specmax, specmin, intthresh)
        
        # OK we have to try a bit harder,
        # We currently don't understand -ve or zero amps
        
        self.passnum += 1
        if minamp <= 0.0:
            raise FindProfileError(ERR_ZEROAMPS)
        
        # Refine list of maxima and minima to be ones above significance threshold
        # (Remember we are always working with a list of indices into the original
        # wavelength and amplitude arrays)
        
        threshamp = (maxamp - minamp) * sigthreash + minamp
        sigmax = specmax[amps[specmax] >= threshamp]
        sigmin = specmin[amps[specmin] >= threshamp]
        print "Sigmax =", sigmax, "Sigmin =", sigmin
 
        # If we can't find a maximum now we can't currently figure it out
        
        if len(sigmax) == 0:
             raise FindProfileError(ERR_NOSIGMAXES)
         
        if len(sigmax) > 2:
            self.maxima = sigmax
            self.minima = sigmin
            raise FindProfileError(ERR_EXCESSMAXES)
        
        # If only one maximum, we think we're OK if we don't have any minima, otherwise we are confused
        
        if len(sigmax) == 1:
            if len(sigmin) == 0:
                return self.setresult(sigmax, sigmin, intthresh)
            self.maxima = sigmax
            self.minima = sigmin
            raise FindProfileError(ERR_EXCESSMINS)
        
        # Case where we have two maxima
        # If we have one minimum in between we are probably OK
        # If we have several choose the minimum one.
        
        lhmax, rhmax = sigmax
        
        possmins = specmin[(lhmax < specmin) & (specmin < rhmax)]
        
        if len(possmins) == 1:
            return self.setresult(sigmax, possmins, intthresh)
        
        self.passnum += 1
        
        if len(possmins) > 1:
            return self.setresult(sigmax, possmins[np.argsort(amps[possmins])[0:1]], intthresh)
        
        # Final effort where we didn't find a minimum between the two maxima
        # Fit a polynomial between the two maxima and find the minimum minimum between those
        
        self.passnum += 1
        
        if lhmax >= rhmax - 5:
            self.maxima = sigmax
            raise FindProfileError(ERR_TOOFEWPTS)
        
        restrwl = offset_wls[lhmax:rhmax+1]
        restamp = amps[lhmax:rhmax+1]
        coeffs = np.polyfit(restrwl, restamp, self.degfit)
        pvals = np.polyval(coeffs, restrwl)
        
        # For time being just get lowest value of pvals
        # Add back lhmax to get index in original array
        
        minv = np.argsort(pvals)[0:1] + lhmax
        
        return self.setresult(sigmax, minv, intthresh)
