# Get details about astro objects from SIMBAD if possible

import pycurl
from StringIO import StringIO
import re

rvmatch = re.compile('^V\s*\(km/s\)\s*([-.\d]+)', re.MULTILINE)

def geturlbody(url):
    """Return buody of url specified"""

    buffer = StringIO()
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

    bod = search_simbad(item)
    if len(bod) == 0:
        return 0.0
    mtc = rvmatch.search(bod)
    if not mtc:
        return 0.0
    return float(mtc.group(1))
