# Use Simbad and astropy/astroquery to get object name from coords and vice versa

from astroquery.simbad import Simbad
from astropy import coordinates
import astropy.units as u

def coord2obs(ra, dec, radius=2, objtype = None):
    """Get objects within given radius of given ra/dec as decimal degrees.
    If object type given, restrict to that"""
    
    sk = coordinates.SkyCoord(ra=ra, dec=dec, unit=u.deg)
    rad = radius * u.arcmin
    sb = Simbad()
    sb.add_votable_fields('otype')
    sres = sb.query_region(sk, radius=rad)
    ids = sres['MAIN_ID'][:]
    if objtype is None:
        return ids
    otypes = sres['OTYPE'][:]
    resids = []
    for ob,nxt in zip(otypes,ids):
        if ob in objtype:
            resids.append(nxt)
    return resids

def obs2coord(obj):
    """Get coordinates of object as (ra, dec) decimals"""
    
    sb = Simbad().query_object(obj)
    if sb is None: return None
    sk = coordinates.SkyCoord(ra=sb['RA'][0], dec=sb['DEC'][0], unit=(u.hour,u.deg))
    return (sk.ra.deg, sk.dec.deg)
     