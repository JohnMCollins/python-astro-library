# @Author: John M Collins <jmc>
# @Date:   2018-06-25T21:17:41+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjinfo.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-17T22:48:34+00:00

# routines for object info database

import re
from astropy.time import Time
from astropy.coordinates import SkyCoord
import datetime
import astropy.units as u
import miscutils
import numpy as np
import pymysql
import sys

DEFAULT_APSIZE = 6
Possible_filters = 'girzHJK'


class  ObjDataError(Exception):
    """Class to report errors concerning individual objects"""
    pass


def get_objname(dbcurs, alias):
    """Return unchanged name if if a main object name, otherwise find object name from alias"""
    dbcurs.execute("SELECT COUNT(*) FROM objdata WHERE objname=%s", alias)
    f = dbcurs.fetchall()
    if f[0][0] != 0:
        return alias
    dbcurs.execute("SELECT objname FROM objalias WHERE alias=%s", alias)
    f = dbcurs.fetchall()
    try:
        return  f[0][0]
    except IndexError:
        raise ObjDataError("Unknown object or alias name", alias)


class ObjAlias(object):
    """Representation of the alias of an object"""

    def __init__(self, aliasname=None, objname=None, source=None, sbok=True):
        self.objname = objname
        self.aliasname = aliasname
        self.source = source
        self.sbok = sbok

    def get(self, dbcurs, aliasname=None):
        """Get alias from aliasname or already supplied one if not given"""

        if aliasname is None:
            aliasname = self.aliasname
        else:
            self.aliasname = aliasname

        if aliasname is None:
            raise ObjDataError("No alias name provided in ObjAlias object", "")

        dbcurs.execute("SELECT objname,source,sbok FROM objalias WHERE alias=%s", aliasname)
        f = dbcurs.fetchall()
        if len(f) == 0:
            raise ObjDataError("Alias not found", aliasname)
        self.objname, self.source, self.sbok = f[0]

    def put(self, dbcurs):
        """Write out alias to file"""

        if self.aliasname is None:
            raise ObjDataError("No alias name given", "")
        if self.objname is None:
            raise ObjDataError("No object name given for alias", self.aliasname)
        if self.source is None:
            raise ObjDataError("No source given for alias", self.aliasname)
        fieldnames = []
        fieldvalues = []
        conn = dbcurs.connection
        fieldnames.append("alias")
        fieldvalues.append(conn.escape(self.aliasname))
        fieldnames.append("objname")
        fieldvalues.append(conn.escape(self.objname))
        fieldnames.append("source")
        fieldvalues.append(conn.escape(self.source))
        fieldnames.append("sbok")
        if self.sbok:
            fieldvalues.append("1")
        else:
            fieldvalues.append("0")
        try:
            dbcurs.execute("INSERT INTO objalias (" + ",".join(fieldnames) + ") VALUES (" + ",".join(fieldvalues) + ")")
        except pymysql.MySQLError as e:
            if e.args[0] == 1062:
                raise ObjDataError("Duplicate alias " + self.aliasname + " object", self.objname)
            else:
                raise ObjDataError("Could not insert alias " + self.aliasname, e.args[1])

    def update(self, dbcurs):
        """Update object to database"""
        if self.aliasname is None:
            raise ObjDataError("No alias in ObjAlias", "")

        conn = dbcurs.connection
        fields = []
        if self.objname is not None:
            fields.append("objname=" + conn.escape(self.objname))
        if self.source is not None:
            fields.append("source=" + conn.escape(self.source))
        if self.sbok:
            fields.append("sbok=1")
        else:
            fields.append("sbok=0")

        try:
            dbcurs.execute("UPDATE objalias SET" + ",".join(fields) + " WHERE alias=" + conn.escape(self.aliasname))
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not update alias " + self.aliasname, e.args[1])

    def delete(self, dbcurs):
        """Delete alias"""
        if self.aliasname is None:
            raise ObjDataError("No alias in ObjAlias", "")
        n = 0
        try:
            n = dbcurs.execute("DELETE FROM objalias WHERE alias=%s", self.aliasname)
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not delete alias " + self.aliasname, e.args[1])
        if n == 0:
            raise ObjDataError("No alias to delete of name", self.aliasname)


class ObjData(object):
    """Decreipt an individaul object"""

    def __init__(self, objname=None, objtype=None, dispname=None):
        self.objname = self.dispname = objname
        self.objtype = objtype
        if dispname is not None:
            self.dispname = dispname
        self.vicinity = None
        self.dist = self.rv = self.ra = self.dec = self.rapm = self.decpm = None
        self.gmag = self.imag = self.rmag = self.zmag = self.Hmag = self.Jmag = self.Kmag = None
        self.apsize = DEFAULT_APSIZE
        self.usable = True

    def get(self, dbcurs, name=None):
        """Get object by name"""

        if name is None:
            name = self.objname
            if name is None:
                raise ObjDataError("No name supplied for ObjData", "")
        dbcurs.execute("SELECT objname,objtype,dispname,vicinity,dist,rv,radeg,decdeg,rapm,decpm,gmag,imag,rmag,zmag,Hmag,Jmag,Kmag,apsize,usable FROM objdata WHERE objname=%s", get_objname(dbcurs, name))
        f = dbcurs.fetchall()
        if len(f) != 1:
            if len(f) == 0:
                raise ObjDataError("(warning) Object not found", name)
            else:
                raise ObjDataError("Internal problem too many objects with name", name)
        self.objname, self.objtype, self.dispname, self.vicinity, self.dist, self.rv, self.ra, self.dec, self.rapm, self.decpm, self.gmag, self.imag, self.rmag, self.zmag, self.Hmag, self.Jmag, self.Kmag, self.apsize, self.usable = f[0]

    def is_target(self):
        """Report if it's the target by comparing with vicinity"""
        return  self.objname == self.vicinity

    def put(self, dbcurs):
        """Save object to database"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        if self.dispname is None:
            raise ObjDataError("No display name in ObjData for", self.objname)
        if self.vicinity is None:
            raise ObjDataError("No vicinity in ObjData for", self.objname)
        if self.ra is None or self.dec is None:
            raise ObjDataError("No coords in ObjData for", self.objname)
        conn = dbcurs.connection
        fieldnames = []
        fieldvalues = []

        fieldnames.append("objname")
        fieldvalues.append(conn.escape(self.objname))
        fieldnames.append("dispname")
        fieldvalues.append(conn.escape(self.dispname))
        fieldnames.append("vicinity")
        fieldvalues.append(conn.escape(self.vicinity))

        if self.objtype is not None:
            fieldnames.append("objtype")
            fieldvalues.append(conn.escape(self.objtype))

        if self.dist is not None:
            fieldnames.append("dist")
            fieldvalues.append("%.6g" % self.dist)

        if self.rv is not None:
            fieldnames.append("rv")
            fieldvalues.append("%.6g" % self.rv)

        fieldnames.append("radeg")
        fieldvalues.append("%.6g" % self.ra)
        fieldnames.append("decdeg")
        fieldvalues.append("%.6g" % self.dec)

        if self.rapm is not None:
            fieldnames.append("rapm")
            fieldvalues.append("%.6g" % self.rapm)
        if self.decpm is not None:
            fieldnames.append("decpm")
            fieldvalues.append("%.6g" % self.decpm)

        for f in Possible_filters:
            aname = f + "mag"
            val = getattr(self, aname, None)
            if val is not None:
                fieldnames.append(aname)
                fieldvalues.append("%.6g" % val)

        fieldnames.append("apsize")
        fieldvalues.append("%d" % self.apsize)
        fieldnames.append("usable")
        if self.usable:
            fieldvalues.append("1")
        else:
            fieldvalues.append("0")

        try:
            dbcurs.execute("INSERT INTO objdata (" + ",".join(fieldnames) + ") VALUES (" + ",".join(fieldvalues) + ")")
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not insert object " + self.objname, e.args[1])

    def update(self, dbcurs):
        """Update object to database"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")

        conn = dbcurs.connection
        fields = []
        if self.dispname is not None:
            fields.append("dispname=" + conn.escape(self.dispname))
        if self.vicinity is not None:
            fields.append("vicinity=" + conn.escape(self.vicinity))
        if self.objtype is not None:
            fields.append("objtype=" + conn.escape(self.objtype))
        if self.dist is not None:
            fields.append("dist=%.6g" % self.dist)
        if self.rv is not None:
            fields.append("rv=%.6g" % self.rv)
        if self.ra is not None:
            fields.append("radeg=%.6g" % self.ra)
        if self.dec is not None:
            fields.append("decdeg=%.6g" % self.dec)
        if self.rapm is not None:
            fields.append("rapm=%.6g" % self.rapm)
        if self.decpm is not None:
            fields.append("decpm=%.6g" % self.decpm)
        for f in Possible_filters:
            aname = f + "mag"
            val = getattr(self, aname, None)
            if val is not None:
                fields.append("%s=%.6g" % (aname, val))
        fields.append("apsize=%d" % self.apsize)
        if self.usable:
            fields.append("usable=1")
        else:
            fields.append("usable=0")

        try:
            dbcurs.execute("UPDATE objdata SET " + ",".join(fields) + " WHERE objname=" + conn.escape(self.objname))
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not update object " + self.objname, e.args[1])

    def delete(self, dbcurs):
        """Delete data for object and also delete aliases for it"""

        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")

        n = 0
        try:
            dbcurs.execute("DELETE FROM objalias WHERE objname=%s", self.objname)
            n = dbcurs.execute("DELETE FROM objdata WHERE objname=%s", self.objname)
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not delete object " + self.objname, e.args[1])
        if n == 0:
            raise ObjDataError("No objects to delete of name", self.objname)

    def list_aliases(self, dbcurs, manonly=False):
        """Get a list of aliases for the object. If manonly is set just list manually entered ones"""

        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")

        dbcurs.execute("SELECT alias,source,sbok FROM objalias WHERE objname=%s", self.objname)
        f = dbcurs.fetchall()
        result = []
        for alias, source, sbok in f:
            if manonly and sbok:
                continue
            result.append(ObjAlias(aliasname=alias, objname=self.objname, source=source, sbok=sbok))
        return  result

    def add_alias(self, dbcurs, aliasname, source, sbok=True):
        """Add an alias"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        ObjAlias(aliasname=aliasname, objname=self.objname, source=source, sbok=sbok).put(dbcurs)

    def delete_aliases(self, dbcurs):
        """Delete all aliases - do this when we recreate list"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        dbcurs.execute("DELETE FROM objalias WHERE objname=%s", self.objname)

    def apply_motion(self, obstime):
        """Apply proper motion (mostly) to coordinates"""

        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        if self.ra is None or self.dec is None:
            raise ObjDataError("No coordinates found in objdata for", self.objname)
        if self.rapm is None or self.decpm is None:
            return
        args = dict(ra=self.ra * u.deg, dec=self.dec * u.deg, obstime=Time('J2000'), pm_ra_cosdec=self.rapm * u.mas / u.yr, pm_dec=self.decpm * u.mas / u.yr)
        if self.dist is not None:
            args['distance'] = self.dist * u.lightyear
        if self.rv is not None:
            args['radial_velocity'] = self.rv * u.km / u.second
        spos = SkyCoord(**args).apply_space_motion(new_obstime=Time(obstime))
        self.ra = spos.ra.deg
        self.dec = spos.dec.deg
        if self.dist is not None:
            self.dist = spos.distance.lightyear


def get_objects(dbcurs, vicinity, obstime=None):
    """Get a list of objects in vicinity of named object
    Adjust for time if specified"""

    targname = get_objname(dbcurs, vicinity)  # Might give error if unknown
    dbcurs.execute("SELECT objname FROM objdata WHERE vicinity=%s", targname)
    onames = dbcurs.fetchall()

    results = []
    targobj = None

    for oname, in onames:
        obj = ObjData(oname)
        obj.get(dbcurs)
        if obj.is_target():
            targobj = obj
        else:
            results.append(obj)
    if targobj is None:
        raise ObjDataError("Could not find target objaect looking for", targname)
    results.insert(0, targobj)

    if obstime is not None:
        for r in results:
            r.apply_motion(obstime)
    return results


def prune_objects(objlist, ras, decs):
    """Prune list of objects to those within ranges of ras and decs given"""
    minra = min(ras)
    maxra = max(ras)
    mindec = min(decs)
    maxdec = max(decs)
    return [o for o in objlist if minra <= o.ra <= maxra and mindec <= o.dec <= maxdec]
