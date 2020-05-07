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


def parsedate(dat):
    """Parse an argument date and try to interpret common things"""
    if dat is None:
        return None
    now = datetime.datetime.now()
    rnow = datetime.datetime(now.year, now.month, now.day)
    m = re.match("(\d+)\D(\d+)(?:\D(\d+))?", dat)
    try:
        if m:
            dy, mn, yr = m.groups()
            dy = int(dy)
            mn = int(mn)
            if yr is None:
                yr = now.year
                ret = datetime.datetime(yr, mn, dy)
                if ret > rnow:
                    ret = datetime.datetime(yr - 1, mn, dy)
            else:
                yr = int(yr)
                if dy > 31:
                    yr = dy
                    dy = int(m.group(3))
                if yr < 50:
                    yr += 2000
                elif yr < 100:
                    yr += 1900
                ret = datetime.datetime(yr, mn, dy)
        elif dat == 'today':
            ret = rnow
        elif dat == 'yesterday':
            ret = rnow - datetime.timedelta(days=1)
        else:
            m = re.match("t-(\d+)$", dat)
            if m:
                ret = rnow - datetime.timedelta(days=int(m.group(1)))
            else:
                raise ValueError("Could not understand date: " + dat)
    except ValueError:
        raise ValueError("Could not understand date: " + dat)

    return ret.strftime("%Y-%m-%d")
