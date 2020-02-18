# Parse time and date string in various formats

import datetime
import re

parset = re.compile('(\d+).(\d+).(\d+)(?:\D+(\d+).(\d+).(\d+)(\.\d+)?)?$')


def parsetime(arg, atend=False):
    """Parse time given as yy/mm/dd or dd/mm/yyyy followewd by optional time.
    If no time given put start of day unless atend is set when put end of day"""

    m = parset.match(arg)
    if m is None:
        raise ValueError("Unknown date format")
    dparts = m.groups()
    if dparts[3] is None:
        yr, mon, day = [int(x) for x in dparts[0:3]]
        if atend:
            hr = 23
            mn = sec = 59
            usec = 999999
        else:
            hr = mn = sec = usec = 0
    else:
        yr, mon, day, hr, mn, sec = [int(x) for x in dparts[0:-1]]
        if dparts[-1] is None:
            usec = 0
        else:
            usec = int(round(float(dparts[-1]) * 1e6))
    if day > 31:
        t = yr
        yr = day
        day = t
    return  datetime.datetime(yr, mon, day, hr, mn, sec, usec)
