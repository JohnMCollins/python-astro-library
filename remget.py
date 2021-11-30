# Get FITS file from REM archives as byte string stream

"""Routines for fetching FITS files"""

import io
import pycurl


class RemGetError(Exception):
    """Throw this exception if we have trouble"""


root_url = 'http://ross.iasfbo.inaf.it'


def get_rest(fullname):
    """Do the result of the job after constructinve the full name"""

    buffer = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, root_url + fullname)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    rcode = c.getinfo(c.RESPONSE_CODE)
    if rcode != 200:
        raise RemGetError("Error %s fetching FITS file" % rcode)
    c.close()
    body = buffer.getvalue()
    if len(body) < 10000 or body[0:6] == b'<html>':
        raise RemGetError("FITS file not found " + fullname)
    return body


def get_obs(fname, remir=False):
    """Get observation file as byte string"""

    if remir:
        fullfname = "Remir/" + fname
    else:
        fullfname = "Ross/" + fname

    return  get_rest("/RossDB/fits_retrieve.php?ffile=/" + fullfname)


def get_iforb(fname):
    """Get individual flat or bias file"""

    return get_rest("/REMDBdev/fits_retrieve.php?ffile=/Ross/" + fname)


def get_saved_fits(dbcurs, ind):
    """Get FITS file when we've saved a copy"""
    if ind == 0:
        raise RemGetError("Attempting load FITS with zero ind")
    dbcurs.execute("SELECT fitsgz FROM fitsfile WHERE ind=%d" % ind)
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        raise RemGetError("Cannot find fits file id " + str(id))
    return  rows[0][0]


def get_obs_fits(dbcurs, obsind):
    """Get FITS file from either our copy or remote"""
    dbcurs.execute("SELECT dithID,ind,ffname FROM obsinf WHERE obsind=%d" % obsind)
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        raise RemGetError("Unable to locate obs ind %d" % obsind)
    dith, ind, ffname = rows[0]
    if ind != 0:
        return  get_saved_fits(dbcurs, ind)
    return  get_obs(ffname, dith != 0)


def get_iforb_fits(dbcurs, iforbind):
    """Get FITS file for bias or flat from either our copy or remote"""
    dbcurs.execute("SELECT ind,ffname FROM iforbinf WHERE iforbind=%d" % iforbind)
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        raise RemGetError("Unable to locate iforb ind %d" % iforbind)
    ind, ffname = rows[0]
    if ind != 0:
        return  get_saved_fits(dbcurs, ind)
    return  get_iforb(ffname)


def set_rejection(dbcurs, obsind, reason, table="obsinf", column="obsind"):
    """Set rejection reason for FITS file"""
    dbcurs.execute("UPDATE %s " % table + "SET rejreason=%s" + " WHERE %s=%d" % (column, obsind), reason)
    dbcurs.connection.commit()


def delete_fits(dbcurs, ind):
    """Delete all references to FITS from database"""
    dbcurs.execute("DELETE FROM fitsfile WHERE ind=%d" % ind)
    dbcurs.execute("UPDATE obsinf SET ind=0 WHERE ind=%d" % ind)
    dbcurs.execute("UPDATE iforbinf SET ind=0 WHERE ind=%d" % ind)
    dbcurs.connection.commit()
