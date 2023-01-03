"""Parse time and date string in various formats"""

import datetime
import re

pallm = re.compile('(\d\d\d\d)-(\d+)$')
poff = re.compile(".?-(\d+)$")
prange = re.compile(r'(\d+(\D)\d+\2\d+(?:\D{1,4}\d+(\D)\d+(?:\3\d+(?:\.\d+)?)?)?)?\D(\d+(\D)\d+\5\d+(?:\D{1,4}\d+(\D)\d+(?:\6\d+(?:\.\d+)?)?)?)?$')
pdatetime = re.compile(r'(\d+)(\D)(\d+)\2(\d+)(?:\D{1,4}(\d+)(\D)(\d+)(?:\6(\d+)(?:\.(\d+))?)?)?$')

def parse_datetime(st):
    """Parse a date and possibly time field and return appropriate thing"""
    if st is None:
        return  None
    mtch = pdatetime.match(st)
    if mtch is None:
        if st.lower() == "today":
            return  datetime.date.today()
        if st.lower() == "yesterday":
            return  datetime.date.today() - datetime.timedelta(days=1)
        mtch = poff.match(st)
        if mtch is not None:
            return  datetime.date.today() - datetime.timedelta(days=int(mtch.group(1)))
        raise  ValueError("Unknown date/time " + st)
    dy, dummy, mon, year, hr, dummy, mn, sec, usec = mtch.groups()
    dy = int(dy)
    mon = int(mon)
    year = int(year)
    if dy > 31:
        dy, year = year, dy
    if year < 50:
        year += 2000
    elif year < 100:
        year += 1900
    if hr is None:
        return  datetime.date(year, mon, dy)
    hr = int(hr)
    mn = int(mn)
    if sec is None:
        sec = usec = 0
    else:
        sec = int(sec)
        if usec is None:
            usec = 0
        else:
            usec = int(float("0." + usec) * 1e6)
            if usec >= 1000000:
                usec = 999999
    return  datetime.datetime(year, mon, dy, hr, mn, sec, usec)

def parsetime(arg, atend=False):
    """Get time and date, if time not given get the beginning of the day
    unless atend given, when give the last second"""
    if arg is None:
        return  None
    dat = parse_datetime(arg)
    if isinstance(dat, datetime.datetime):
        return  dat
    if atend:
        return  datetime.datetime(dat.year, dat.month, dat.day, 23, 59, 59, 999999)
    return  datetime.datetime(dat.year, dat.month, dat.day, 0, 0, 0, 0)

def parsedate(dat):
    """Parse an argument date and get string date"""
    dt = parse_datetime(dat)
    if dt is None:
        return  None
    return dt.strftime("%Y-%m-%d")

def pack_field(dt, fieldselect, datefield, op):
    """Insert mysql date selection into fieldselect with given op"""
    if dt is None:
        return
    if isinstance(dt, datetime.datetime):
        fieldselect.append("{:s}{:s}'{:%Y-%m-%d %H:%M:%S.%f}'".format(datefield, op, dt))
    else:
        fieldselect.append("DATE({:s}){:s}'{:%Y-%m-%d}'".format(datefield, op, dt))

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
        dstring = daterange
        mtch = prange.match(daterange)
        if mtch:
            pack_field(parse_datetime(mtch.group(1)), fieldselect, datefield, ">=")
            pack_field(parse_datetime(mtch.group(4)), fieldselect, datefield, "<=")
        else:
            pack_field(parse_datetime(daterange), fieldselect, datefield, "=")
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


class DateRangeArg:
    """Date ranges other than in database filed"""

    def __init__(self):
        self.fromdate = datetime.date(1970, 1, 1)
        self.todate = datetime.date(2099, 12, 31)

    def inrange(self, dat):
        """Check in range"""
        if isinstance(dat, datetime.datetime):
            dat = dat.date()
        return self.fromdate <= dat <= self.todate

    def parsearg(self, arg):
        """Parse a command-line argument"""
        datesp = arg.split(':')
        try:
            if len(datesp) != 2:
                self.fromdate = self.todate = parsetime(arg).date()
            else:
                fd, td = datesp
                if len(fd) != 0:
                    self.fromdate = parsetime(fd).date()
                if len(td) != 0:
                    self.todate = parsetime(td).date()
        except ValueError:
            raise ValueError("Did not understand date range " + arg)
        if self.fromdate > self.todate:
            raise ValueError("Date range from > to " + arg)
