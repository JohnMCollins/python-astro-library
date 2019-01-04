# @Author: John M Collins <jmc>
# @Date:   2018-11-08T16:57:12+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dbremfitsobj.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-03T21:06:36+00:00

# Routines for database version of remfits finding

import os
import os.path
import re
from astropy.time import Time
from astropy.io import fits
import datetime
import astropy.units as u
import numpy as np
import math
import random

class  RemObjError(Exception):
    """Class to report errors"""

    def __init__(self, message, warningonly = False):
        super(RemObjError, self).__init__(message)
        self.warningonly = warningonly

class  Remobj(object):
    """Represent remote object found in file"""

    def __init__(self, name = "", pixcol=0, pixrow=0, ra=0.0, dec=0.0):
        self.objname = name
        self.pixcol = pixcol
        self.pixrow = pixrow
        self.ra = ra
        self.dec = dec
        self.apradius = None
        self.aducount = None
        self.aduerror = None

    def sortorder(self):
        """Rough and ready way to sort list"""
        return self.ra * 1000.0 + self.dec + 90.0

class  Remobjlist(object):
    """Represent list of above objects"""

    def __init__(self, filename = "", obsdate = None, filter = None):
        self.filename = filename
        self.obsdate = obsdate
        self.filter = filter
        self.target = None
        self.objlist = []
        self.airmass = None
        self.skylevel = None
        self.percentile = None

    def __hash__(self):
        try:
            return  int(round(self.obsdate * 1e6))
        except TypeError:
            raise RemObjError("Incomplete observation type")

    def addtarget(self, obj):
        """Set target"""
        oldtarget = self.target
        self.target = obj
        if oldtarget is not None:
            raise RemObjError("Target was already set to " + oldtarget.objname, True)

    def addobj(self, obj):
        """Add object to list"""
        self.objlist.append(obj)
        self.objlist.sort(key=lambda x: x.sortorder())

class  RemobjSet(object):
    """Class to remember a whole set of obs"""

    def __init__(self, targname = None):
        self.filename = None
        self.xmldoc = None
        self.xmlroot = None
        self.basedir = os.getcwd()
        self.targname = targname
        self.obslookup = dict()

    def addobs(self, obs, updateok = False):
        """Add obs results to list. forbid updating unless updateok given"""
        if obs in self.obslookup and not updateok:
            raise RemObjError("Already got obs for date %.6f filter %s" % (obs.obsdate, obs.filter))
        obs.filename = os.path.abspath(obs.filename)
        obs.set_basedir(os.path.dirname(obs.filename), self.basedir)
        self.obslookup[obs] = obs

    def getobslist(self, filter = None, adjfiles = True, firstdate = None, lastdate = None, resultsonly = False):
        """Get a list of observations for processing, in date order.
        If filter specified, restrict to those
        adjust files to be relative to current directory if adjfiles set"""
        oblist = list(self.obslookup.values())
        if resultsonly:
            oblist = [x for x in oblist if x.skylevel is not None]
        if filter is not None:
            oblist = [x for x in oblist if x.filter == filter ]
        if firstdate is not None:
            oblist = [x for x in oblist if x.obsdate >= firstdate ]
        if lastdate is not None:
            oblist = [x for x in oblist if x.obsdate <= lastdate ]
        oblist.sort(key = lambda x: x.obsdate)
        if adjfiles:
            cwd = os.getcwd()
            if cwd != self.basedir:
                for ob in oblist:
                    ob.set_basedir(self.basedir, cwd)
        return oblist

def getfits(dbcurs, id):
    """Fetch FITS.gz file of given ID from database"""
    dbcurs.execute("SELECT fitsgz FROM fitsfile WHERE ind=" + str(id))
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        raise RemObjError("Cannot find fits file id " + str(id))
    tname = "tmpfits-%.9d.gz" % random.randint(0,999999999)
    fout = open(tname, 'wb')
    fout.write(rows[0][0])
    fout.close()
    rows = None
    ffile = fits.open(tname, memmap=False, lazy_load_hdus=False)
    os.unlink(tname)
    return ffile

class ForB(object):
    """Description of flat or bias file"""

    def __init__(self, year, month, type, filter, fitsind, diff = 0):
        self.year = year
        self.month = month
        self.type = type
        self.filter = filter
        self.fitsind = fitsind
        self.diff = diff

def get_nearest_forbinf(dbcurs, year, month):
    """This routine gets information about flat or bias files for the nearest month to that specified

    return (flat dict, bias dict)"""
    ym = year * 12 + month
    dbcurs.execute("SELECT year,month,typ,filter,fitsind,ABS(CONVERT(year,SIGNED)*12 + CONVERT(month, SIGNED)-"+str(ym)+") AS diff FROM forbinf ORDER BY diff,typ,filter LIMIT 16")
    rows = dbcurs.fetchall()
    fdict = dict()
    bdict = dict()
    for row in rows:
        poss = ForB(row[0], row[1], row[2], row[3], row[4], row[5])
        if poss.type == 'flat':
            if poss.filter not in fdict:
                fdict[poss.filter] = poss
        elif poss.filter not in bdict:
            bdict[poss.filter] = poss
    if len(fdict) != 4:
        raise RemObjError("Could not read complete flat table for year " + str(year) + " month " + str(month))
    if len(bdict) != 4:
        raise RemObjError("Could not read complete bias table for year " + str(year) + " month " + str(month))
    return (fdict, bdict)

def get_rem_obs(dbcurs, target, year, month, filter):
    """Get a list of REM observations of given target name for given year, month and filterself.
    Sort into date order but just return a list of (obsind, fitsind) tuples"""

    # Things are held as different names so kick off by getting a list of everything else
    # that the target might be known as.

    pndict = dict()
    pndict[target] = 1

    dbcurs.execute("SELECT alias FROM objalias WHERE objname=" + dbcurs.connection.escape(target))
    rows = dbcurs.fetchall()
    for row in rows:
        pndict[row[0]] = 1
    quoted_names = ["object=" + dbcurs.connection.escape(z) for z in list(pndict.keys())]
    if len(quoted_names) < 2:
        namesel = quoted_names[0]
    else:
        namesel = "(" + " OR ".join(quoted_names) + ")"
    datesel = "'%.4d-%.2d-01'" % (year, month)
    datesel = "date_obs>=" + datesel + " AND date_obs < DATE_ADD(" + datesel + ",INTERVAL 1 MONTH)"
    dbcurs.execute("SELECT obsind,ind,exptime FROM obsinf WHERE filter=" + dbcurs.connection.escape(filter) + " AND " + datesel + " AND " + namesel + " ORDER BY date_obs")
    return dbcurs.fetchall()

def get_find_results(dbcurs, obsind):
    """See if we did this before.

    return (ok, notok)"""

    dbcurs.execute("SELECT COUNT(*) FROM identobj WHERE obsind=" + str(obsind))
    rows = dbcurs.fetchall()
    ok = rows[0][0]
    dbcurs.execute("SELECT COUNT(*) FROM notfound WHERE obsind=" + str(obsind))
    rows = dbcurs.fetchall()
    nok = rows[0][0]
    return (ok, nok)

def del_find_results(dbcurs, obsind, delfound = True, delnotfound = True):
    """Delete previous observations for obsind"""

    if delfound:
        dbcurs.execute("DELETE FROM identobj WHERE obsind=" + str(obsind))
        dbcurs.execute("DELETE FROM aducalc WHERE obsind=" + str(obsind))
    if delnotfound:
        dbcurs.execute("DELETE FROM notfound WHERE obsind=" + str(obsind))
    dbcurs.connection.commit()

def add_notfound(dbcurs, obsind, target, filter, exptime, comment, notcurrf = False, apsize = None, searchrad = None):
    """Add obsind to list of not found objects with reasons."""

    nffields = ['obsind', 'target', 'filter', 'exptime', 'comment', 'notcurrflat']
    nfvalues = [ str(obsind), dbcurs.connection.escape(target), dbcurs.connection.escape(filter), str(exptime), dbcurs.connection.escape(comment), str(notcurrf)]
    if apsize is not None:
        nffields.append('apsize')
        nfvalues.append(str(apsize))
    if searchrad is not None:
        nffields.append('searchrad')
        nfvalues.append(str(searchrad))
    dbcurs.execute("INSERT INTO notfound (" + ','.join(nffields) + ") VALUES (" + ','.join(nfvalues) + ")")
    dbcurs.connection.commit()

def add_objident(dbcurs, obsind, target, objname, filter, exptime, pixcol, pixrow, radeg, decdeg, apsize, searchrad, notcurrf = False):
    """Add object identification to list of found objects"""
    Fvals = []
    Fvals.append(str(obsind))
    Fvals.append(dbcurs.connection.escape(target))
    Fvals.append(dbcurs.connection.escape(objname))
    Fvals.append(dbcurs.connection.escape(filter))
    Fvals.append(str(exptime))
    Fvals.append(str(pixcol))
    Fvals.append(str(pixrow))
    Fvals.append(str(radeg))
    Fvals.append(str(decdeg))
    Fvals.append(str(apsize))
    Fvals.append(str(searchrad))
    Fvals.append(str(notcurrf))
    dbcurs.execute("INSERT INTO identobj (obsind,target,objname,filter,exptime,pixcol,pixrow,radeg,decdeg,apsize,searchrad,notcurrflat) VALUES (" + ','.join(Fvals) + ")")
    dbcurs.connection.commit()
