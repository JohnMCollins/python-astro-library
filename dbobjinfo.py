# @Author: John M Collins <jmc>
# @Date:   2018-06-25T21:17:41+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjinfo.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-17T22:48:34+00:00

# routines for object info database

import re
from astropy.time import Time
import datetime
import astropy.units as u
import miscutils
import numpy as np
import math
import operator
import sys
from scipy.integrate.odepack import _msgs

DEFAULT_APSIZE = 6

Time_origin = Time('J2000.0')
Time_now = Time(datetime.datetime.now())
Conv_pm = (u.mas / u.yr).to("deg/day")

Objdata_fields = ['objname', 'objtype', 'dispname', 'dist', 'rv', 'radeg', 'rapm', 'raerr', 'decdeg', 'decerr', 'decpm']
for f in 'giruz':
    for ff in ('mag', 'merr'):
        Objdata_fields.append(f + ff)
Objdata_fields.append('apsize')
Objdata_fields = ','.join(Objdata_fields)


class  ObjDataError(Exception):
    """Class to report errors concerning individual objects"""
    pass


class RaDec(object):
    """Class to store RA and Dec in providing for PM and uncertainties

    Always store as degrees [0,360) for RA and [-90,90] for DEC
    PM stored as MAS / yr"""

    def __init__(self, value=None, err=None, pm=None):
        self.value = value
        self.err = err
        self.pm = pm

    def getvalue(self, tfrom=None):
        """Get RA or DEC value alone, adjusting for pm if set,
        in which case take time from parameter (datetime object) or base time if not given"""
        if self.value is None:
            raise ObjDataError("RA/DEC value not defined")
        if self.pm is None or tfrom is None:
            return  self.value
        et = Time(tfrom)
        tdiff = et - Time_origin
        return self.value + self.pm * Conv_pm * tdiff.jd


class Mag(object):
    """Represent a magnitude with filter"""

    def __init__(self, filter=None, val=None, err=None):
        self.value = val
        self.filter = filter
        self.err = err


class Maglist(object):
    """Represents a list of magnitudes with various filters"""

    def __init__(self):
        self.maglist = dict()

    def is_def(self):
        """Return whether any mags defined"""
        return len(self.maglist) != 0

    def get_val(self, filter):
        """get magnitude for given filter"""
        try:
            mg = self.maglist[filter]
            return (mg.value, mg.err)
        except KeyError:
            raise ObjDataError("No magnitude defined for filter " + filter)

    def set_val(self, filter, value, err=None, force=True):
        """Set mag value"""
        if value is None:
            return False
        if force or filter not in self.maglist:
            self.maglist[filter] = Mag(filter, value, err)
            return True
        return False

    def av_val(self):
        """Return average value of magnitude and error as pair"""
        mags = []
        errs = []

        for nxt in list(self.maglist.values()):
            mgs.append(nxt.value)
            errs.append(nxt.err)

        if len(mags) == 0:
            raise ObjDataError("No magnitudes assigned")

        m = np.mean(mags)
        if None in errs:
            e = None
        else:
            e = math.sqrt(np.mean(np.array(errs) ** 2))
        return (m, e)

    def max_val(self):
        """Get maximum value of magnitude, return 0 if not defined"""

        mags = [m.value for m in self.maglist.values()]
        try:
            return min(mags)
        except ValueError:
            return  0


class ObjData(object):
    """Decreipt an individaul object"""

    def __init__(self, objname=None, objtype=None, dispname=None, dist=None, rv=None, ra=None, dec=None):
        self.objname = self.dispname = objname
        self.objtype = objtype
        if dispname is not None:
            self.dispname = dispname
        self.dist = dist
        self.rv = rv
        self.rightasc = RaDec(value=ra)
        self.decl = RaDec(value=dec)
        self.apsize = None
        self.maglist = Maglist()

    def get_ra(self, tfrom=None):
        """Get RA value"""
        return  self.rightasc.getvalue(tfrom)

    def get_dec(self, tfrom=None):
        """Get DECL value"""
        return  self.decl.getvalue(tfrom)

    def set_ra(self, **kwargs):
        """Set RA value"""
        self.rightasc = RaDec(**kwargs)

    def set_dec(self, **kwargs):
        """Set RA value"""
        self.decl = RaDec(**kwargs)

    def update_ra(self, value=None, err=None, pm=None):
        """Update RA value"""
        if value is not None:
            self.rightasc.value = value
        if err is not None:
            self.rightasc.err = value
        if pm is not None:
            self.rightasc.pm = value

    def update_dec(self, value=None, err=None, pm=None):
        """Update DECL value"""
        if value is not None:
            self.decl.value = value
        if err is not None:
            self.decl.err = value
        if pm is not None:
            self.decl.pm = value

    def get_aperture(self, defval=DEFAULT_APSIZE):
        """Retrun aperture size of object or default value"""
        if self.apsize is None:
            return defval
        return self.apsize

    def set_apsize(self, value):
        """Set aperture size"""
        self.apsize = value

    def get_mag(self, filter=None):
        """Get magnitude for given filter or average"""
        if filter is None:
            return self.maglist.av_val()
        return self.maglist.get_val(filter)

    def get_maxmag(self):
        """Get maximum magnitude"""
        return self.maglist.max_val()

    def set_mag(self, filter, value, err=None, force=True):
        """Set magnitude for given filter"""
        return self.maglist.set_val(filter, value, err, force)

    def load_dbrow(self, dbrow):
        """Load from row of database in order given in Objdata_fields"""
        dbrow = list(dbrow)
        self.objname = dbrow.pop(0)
        self.objtype = dbrow.pop(0)
        self.dispname = dbrow.pop(0)
        self.dist = dbrow.pop(0)
        try:
            self.rv = float(dbrow.pop(0))
        except (TypeError, ValueError):
            self.rv = None
        v = dbrow.pop(0); e = dbrow.pop(0); pm = dbrow.pop(0)
        self.update_ra(value=v, err=e, pm=pm)
        v = dbrow.pop(0); e = dbrow.pop(0); pm = dbrow.pop(0)
        self.update_dec(value=v, err=e, pm=pm)
        for f in 'giruz':
            v = dbrow.pop(0); e = dbrow.pop(0)
            self.set_mag(filter=f, value=v, err=e)
        self.apsize = dbrow.pop(0)

    def add_object(self, dbcurs):
        """Add new object to database"""

        fieldlist = ['objname', "dispname"]
        fieldvalues = []

        conn = dbcurs.connection

        if self.objname is None:
            raise ObjDataError("Trying to save undefined object")

        nam = conn.escape(self.objname)
        fieldvalues.append(nam)
        fieldvalues.append(nam)  # For dispname
        if self.objtype is not None:
            fieldlist.append('objtype')
            fieldvalues.append(conn.escape(self.objtype))
        if self.dist is not None:
            fieldlist.append('dist')
            fieldvalues.append(str(self.dist))
        if self.rv is not None and self.rv != "--":
            fieldlist.append('rv')
            fieldvalues.append(str(self.rv))
        if self.rightasc.value is None:
            raise ObjDataError("Right assension missing from " + self.objname)
        else:
            fieldlist.append('radeg')
            fieldvalues.append(str(self.rightasc.value))
            if self.rightasc.err is not None:
                fieldlist.append('raerr')
                fieldvalues.append(str(self.rightasc.err))
            if self.rightasc.pm is not None:
                fieldlist.append('rapm')
                fieldvalues.append(str(self.rightasc.pm))
        if self.decl.value is None:
            raise ObjDataError("Declinationmissing from " + self.objname)
        else:
            fieldlist.append('decdeg')
            fieldvalues.append(str(self.decl.value))
            if self.decl.err is not None:
                fieldlist.append('decerr')
                fieldvalues.append(str(self.decl.err))
            if self.decl.pm is not None:
                fieldlist.append('decpm')
                fieldvalues.append(str(self.decl.pm))
        if self.apsize is not None:
            fieldlist.append('apsize')
            fieldvalues.append(str(self.apsize))
        for filt in 'giruz':
            try:
                mag, magerr = self.get_mag(filt)
                if mag is not None:
                    fieldlist.append(filt + 'mag')
                    fieldvalues.append(str(mag))
                    if magerr is not None:
                        fieldlist.append(filt + 'merr')
                        fieldvalues.append(str(magerr))
            except ObjDataError:
                continue
        fieldlist = ','.join(fieldlist)
        fieldvalues = ','.join(fieldvalues)
        if dbcurs.execute("INSERT INTO  objdata (" + fieldlist + ") VALUES (" + fieldvalues + ")") != 1:
            raise ObjDataError("Could not insert data to database")

    def update_filters(self, dbcurs):
        """update filter values in existing object"""

        setfs = []
        for filt in 'giruzHJK':
            try:
                mag, magerr = self.get_mag(filt)
                if mag is not None:
                    setfs.append(filt + 'mag=' + str(mag))
                    if magerr is not None:
                        setfs.append(filt + 'merr=' + str(magerr))
            except ObjDataError:
                continue
        if len(setfs) != 0:
            dbcurs.execute("UPDATE objdata SET " + ','.join(setfs) + " WHERE objname=" + dbcurs.connection.escape(self.objname))

    def get_names(self, dbcurs):
        """Get all names and alias of the object with the main name first"""

        if self.objname is None:
            raise ObjDataError("Object not defined yet")

        results = [ self.objname ]
        dbcurs.execute("SELECT alias FROM objalias WHERE objname=" + dbcurs.connection.escape(self.objname))
        rtab = dbcurs.fetchall()
        for r in rtab:
            results.append(r[0])
        return  results

# Time conversion routines


def conv_when(when=None):
    """Convert time (default now) and return (when, tidff) where when is Time object
        and tdiff is Timedelta from J2000"""

    if when is None:
        when = Time_now
    elif type(when) == datetime.datetime:
        when = Time(when)
    elif type(when) == 'float':
        if when >= 2400000.0:
            when = Time(when, format='jd')
        else:
            when = Time(when, format='mjd')
    tdiff = when - Time_origin
    return  (when, tdiff)

# Get object target name from possible aliases


def get_targetname(dbcurs, name):
    """Look up definitive name for object from name given

    dbcurs is cursor to database
    name is name to look up
    Return target name or give exception"""

    mydb = dbcurs.connection
    dbcurs.execute("SELECT COUNT(*) FROM objdata WHERE objname=" + mydb.escape(name))
    rows = dbcurs.fetchall()
    nobj = rows[0][0]
    if nobj > 0:
        if nobj > 1:
            raise ObjDataError("confused by " + str(nobj) + " objects with name " + name)
        return  name
    nobj = dbcurs.execute("SELECT objname FROM objalias WHERE alias=" + mydb.escape(name))
    if nobj != 1:
        if nobj > 1:
            raise ObjDataError("confused by " + str(nobj) + " objects with alias " + name)
        else:
            raise ObjDataError("cannot find any objects with name or alias " + name)
    rows = dbcurs.fetchall()
    return  rows[0][0]


def is_defined(dbcurs, name):
    """Report whether given name is defined"""
    try:
        get_targetname(dbcurs, name)
        return True
    except ObjDataError:
        return False

# Generate MySQL query to get objects in given location adjusting for PM


def gen_query(ra, dec, radius, when=None):
    """Generate query for list of objects within given radius

    args are:
        ra - right ascension in degrees
        dec - declination in degrees
        radius - radius in arcmin
        when - time to adjust for PMs in default today
        Return query string ready to tack on to MySQL select"""

    when, tdiff = conv_when(when)
    rsq = (radius * u.arcmin).to('deg').to_value() ** 2
    pmconv = tdiff.jd * Conv_pm
    return "POWER(radeg + rapm * " + str(pmconv) + " - " + str(ra) + ", 2) + POWER(decdeg + decpm * " + str(pmconv) + " - " + str(dec) + ", 2) <= " + str(rsq)


def get_objlist(dbcurs, ra, dec, radius, when=None):
    """Get object list of tupes (adjra, adjdec, object) in adjra, adjdec order

    Args are:

        dbcurse - cursor for database
        ra - right ascension of centre point deg
        dec - declination of centre point deg
        radius - radius in arcmin
        when - time to base on default now"""

    when, tdiff = conv_when(when)
    dbcurs.execute("SELECT " + Objdata_fields + " FROM objdata WHERE " + gen_query(ra, dec, radius, when))
    tab = dbcurs.fetchall()
    result = []
    for row in tab:
        item = ObjData()
        item.load_dbrow(row)
        adjra = item.rightasc.getvalue(when)
        adjdec = item.decl.getvalue(when)
        result.append((adjra, adjdec, item))
    result.sort(key=operator.itemgetter(0, 1))
    return result


def get_object(dbcurs, name):
    """Get details of object by name"""

    dbcurs.execute("SELECT " + Objdata_fields + " FROM objdata WHERE objname=" + dbcurs.connection.escape(name))
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        raise ObjDataError("Could not find object " + name)
    result = ObjData()
    result.load_dbrow(rows[0])
    return result


def add_alias(dbcurs, name, alias, source):
    """Add a single alias to name"""
    conn = dbcurs.connection
    values = [ conn.escape(name), conn.escape(alias), conn.escape(source) ]
    dbcurs.execute("INSERT INTO objalias (objname,alias,source) VALUES (" + ','.join(values) + ")")


def del_object(dbcurs, nameorobj):
    """Delete object and its aliases from database.
    Object is given by structure ret or name"""
    name = nameorobj
    if type(name) is not str:
        name = nameorobj._objname
    qname = dbcurs.connection.escape(name)
    dbcurs.execute("DELETE FROM objdata WHERE objname=" + qname)
    dbcurs.execute("DELETE FROM objalias WHERE objname=" + qname)
