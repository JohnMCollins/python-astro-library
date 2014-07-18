# Convert to/from Julian dates
# Algs from http://mathforum.org/library/drmath/view/51907.html

import datetime
import math

class UTC(datetime.tzinfo):
    """Implementation of dates in UTC only"""

    def utcoffset(self, dt):
        return 0
    def dst(self, dt):
        return None
    def tzname(self):
        return "UTC"

utc = UTC()

def jdate_to_datetime(jd):
    """Convert Julian Date to Datetime structure"""

    if jd >= 1e6:
        fr, J = math.modf(jd + 0.5)
        J = int(J + 0.5)
    else:
        fr, J = math.modf(jd)
        J = int(J) + 2400001

    p = J + 68569
    q = 4 * p / 146097
    r = p - (146097 * q + 3) / 4
    s = 4000 * (r + 1) / 1461001
    t = r - 1461 * s / 4 + 31
    u = 80 * t / 2447
    v = u / 11

    yyyy = 100 * (q - 49) + s + v
    mm = u + 2 - 12 * v
    dd = t - 2447 * u / 80

    fr += .5 / (24.0 * 3600e6)
    fr *= 24.0
    fr, hour = math.modf(fr)
    fr *= 60.0
    fr, minute = math.modf(fr)
    fr *= 60.0
    fr, second = math.modf(fr)
    fr *= 1e6
    fr, microsec = math.modf(fr)
    return datetime.datetime(yyyy, mm, dd, int(hour), int(minute), int(second), int(microsec), tzinfo=utc)

def datetime_to_jdate(dt, modified = True):
    """Convert datetime structure to Julian Date"""
    m1 = (dt.month - 14) / 12
    y1 = (dt.year + 4800)
    jd = 1461 * (y1+m1) / 4 + 367 * (dt.month-2-12*m1)/ 12 - (3 * ((y1+m1+100)/100)) / 4 + dt.day - 32076
    if modified:
        jd -= 2400000
        jd = float(jd)
    else:
        jd += 0.5
    tim = (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    return jd + tim


        

