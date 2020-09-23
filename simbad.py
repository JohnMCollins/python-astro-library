# Get details about astro objects from SIMBAD if possible

import pycurl
from io import BytesIO
import re

rvmatch = re.compile('^V\s*\(km/s\)\s*([-.\d]+)', re.MULTILINE)


def geturlbody(url):
    """Return buody of url specified"""

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return  body


def search_simbad(item):
    """Search Simbad for specified item"""

    return  geturlbody('http://simbad.u-strasbg.fr/simbad/sim-basic?Ident=' + item + '&submit=SIMBAD+search')


def getrv(item):
    """Search SIMBAD database for item name and return RV"""
    bod = search_simbad(item)
    if len(bod) == 0:
        return None
    mtc = rvmatch.search(bod.decode())
    if not mtc:
        return None
    return float(mtc.group(1))
