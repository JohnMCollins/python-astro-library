# Parse time and date string in various formats

import datetime
import re

parset = re.compile('(\d+).(\d+).(\d+)(?:\D+(\d+).(\d+).(\d+)(\.\d+)?)?$')
pallm = re.compile('(\d\d\d\d)-(\d+)$')
pdat = re.compile("(\d+)\D(\d+)(?:\D(\d+))?")
poff = re.compile("t-(\d+)$")


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
    m = pdat.match(dat)
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
            m = poff.match(dat)
            if m:
                ret = rnow - datetime.timedelta(days=int(m.group(1)))
            else:
                raise ValueError("Could not understand date: " + dat)
    except ValueError:
        raise ValueError("Could not understand date: " + dat)

    return ret.strftime("%Y-%m-%d")


def parsedaterange(fieldselect, daterange=None, allmonth=None, datefield='date_obs'):
    """Parse date range or all month specification and set up part of a MySQL field select
    statement into array "fieldselect" (assuming to be joined later by AND).
    Date range can be given in the "daterange" argument as date1:date2 or :date2 or date1:
    or in the allmonth argument as yyyy-mm. Field in datebase can be specified usuually date_obs
    Return a suitable date string or none
    If single argument allow for that beeing y/m/d,h:m:s or such"""

    dstring = None

    if allmonth is not None:
        mtch = pallm.match(allmonth)
        if mtch is None:
            raise ValueError("Cannot understand allmonth arg " + allmonth + "expecting yyyy-mm")
        smonth = allmonth + "-01"
        fieldselect.append("date(" + datefield + ")>='" + smonth + "'")
        fieldselect.append("date(" + datefield + ")<=date_sub(date_add('" + smonth + "',interval 1 month),interval 1 day)")
        dstring = "all month " + allmonth
    elif daterange is not None:
        datesp = daterange.split(':')
        # NB might get ValueError form parsedate, let it happen
        if len(datesp) != 2:
            # Might give specific time as well as date - allow for time delimited by :s
            try:
                dt = parsetime(daterange)
                if dt.hour + dt.minute + dt.second + dt.microsecond != 0:
                    fieldselect.append(datefield + dt.strftime("='%Y-%m-%d %H:%M:%S'"))
                    return daterange
            except ValueError:
                if len(datesp) != 1:
                    raise ValueError("Don't understand what date " + daterange + " is supposed to be")
            fieldselect.append("date(" + datefield + ")='" + parsedate(daterange) + "'")
            dstring = daterange
        else:
            fd, td = datesp
            dstring = ""
            if len(fd) != 0:
                fieldselect.append("date(" + datefield + ")>='" + parsedate(fd) + "'")
                dstring = fd
            if len(td) != 0:
                fieldselect.append("date(" + datefield + ")<='" + parsedate(td) + "'")
                if len(fd) != 0:
                    dstring += " "
                dstring += "up to " + td
            elif len(fd) != 0:
                dstring += " onwards"
            else:
                dstring = "All dates"

    # Don't do anything if neither specified.
    return dstring


def parseargs_daterange(argp):
    """Parse arguments relevant to date range parsing"""
    argp.add_argument('--nodates', action='store_true', help='Include all files without regard to dates')
    argp.add_argument('--dates', type=str, help='From:to dates', default='1/1/2017:')
    argp.add_argument('--allmonth', type=str, help='All of given year-month as alternative to from/to date')


def getargs_daterange(resargs, fieldselect, datefield='date_obs'):
    """Fetch and apply aruguments relevant to date range parsing NB might give ValueError"""
    if not resargs['nodates']:
        return parsedaterange(fieldselect, daterange=resargs['dates'], allmonth=resargs['allmonth'], datefield=datefield)
    return None
