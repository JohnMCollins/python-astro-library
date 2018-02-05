# Use Simbad and astropy/astroquery to get object name from coords and vice versa

from astroquery.simbad import Simbad
from astropy import coordinates
import astropy.units as u
import re
import string

def coord2objs(ra, dec, radius=2, extras = False):
    """Get objects within given radius of given ra/dec as decimal degrees.
    If object type given, restrict to that"""
    
    sk = coordinates.SkyCoord(ra=ra, dec=dec, unit=u.deg)
    rad = radius * u.arcmin
    sb = Simbad()
    sb.add_votable_fields('id', 'otype')
    sres = sb.query_region(sk, radius=rad)
    if sres is None: return []
    ids = [id for id in sres['MAIN_ID']]
    if not extras: return ids
    otypes = [ot for ot in sres['OTYPE']]
    idas = [string.split(oid, ', ') for oid in sres['ID']]
    resids = []
    for n in zip(ids, idas, otypes):
        resids.append(n)
    return resids

def obj2coord(obj):
    """Get coordinates of object as (ra, dec) decimals"""
    
    m = re.match('(\d+z\.\d+)\s*([-+]?\d+\.\d+)', obj)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.match('(\d+)\s+(\d+)\s+(\d+\.\d+)\s+([-+]?\d+)\s+(\d+)\s+(\d+\.\d+)', obj)
    if m:
        sk = coordinates.SkyCoord(m.group(1) + 'h' + m.group(2) + 'm' + m.group(3) + 's ' + m.group(4) + 'd' + m.group(5) + 'm' + m.group(6) + 's')
    else:
        sb = Simbad().query_object(obj)
        if sb is None: return None
        sk = coordinates.SkyCoord(ra=sb['RA'][0], dec=sb['DEC'][0], unit=(u.hour,u.deg))
    return (sk.ra.deg, sk.dec.deg)
