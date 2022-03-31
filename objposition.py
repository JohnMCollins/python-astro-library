"""Identification of an object"""

import datetime
import xml.etree.ElementTree as ET
from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
import xmlutil

# PM units

MAS_YR = u.mas / u.yr


class ObjPositionErr(Exception):
    """Class to raise if we have a problem with object idents"""

    def getmessage(self):
        """Get the message corresponding to the problem"""
        return " - no ".join(self.args)


class ObjPosition:
    """Contains name, display name and object index in database of known object"""

    ObjPosition_attr = ('rv', 'ra', 'dec', 'dist', 'rapm', 'decpm', 'origra', 'origdec', 'origdist')

    def __init__(self, **kwargs):
        self.dist = self.rv = self.ra = self.dec = self.rapm = self.decpm = self.origra = self.origdec = self.origdist = None
        try:
            cobj = kwargs['copyobj']
            for n in ObjPosition.ObjPosition_attr:
                setattr(self, n, getattr(cobj, n))
        except (KeyError, AttributeError):
            pass
        for n in ObjPosition.ObjPosition_attr:
            if n in kwargs:
                setattr(self, n, kwargs[n])

    def check_valid_posn(self):
        """Raise error if not valid for saving"""
        if self.ra is None:
            raise ObjPositionErr("Invalid position", "No RA")
        if self.dec is None:
            raise ObjPositionErr("Invalid position", "No DEC")

    def save_pos(self):
        """Remember original position"""
        self.origra = self.ra
        self.origdec = self.dec
        self.origdist = self.dist

    def put_position(self, fnames, fvalues):
        """Update lists of names and values for insertion into the database"""
        for name, val in (('radeg', self.ra), ('decdeg', self.dec), ('rv', self.rv), ('dist', self.dist), ('rapm', self.rapm), ('decpm', self.decpm)):
            if val is not None:
                fnames.append(name)
                fvalues.apppend("{:.6e}".format(val))

    def update_position(self, fields):
        """Update fields vector to accommodate changes in position info"""
        for name, val in (('radeg', self.ra), ('decdeg', self.dec), ('rv', self.rv), ('dist', self.dist), ('rapm', self.rapm), ('decpm', self.decpm)):
            if val is not None:
                fields.append("{:s}={:.6e}".format(name, val))

    def in_region(self, minra, maxra, mindec, maxdec):
        """Check if object is in region"""
        return  minra <= self.ra <= maxra and mindec <= self.dec <= maxdec

    def apply_motion(self, obstime):
        """Apply proper motion to object for given obs time"""

        if self.rapm is None or self.decpm is None:
            return

        # In case we did this before

        self.ra = self.origra
        self.dec = self.origdec
        self.dist = self.origdist

        # In case we did it as date change to midday on date

        if isinstance(obstime, datetime.date):
            obstime = datetime.datetime(obstime.year, obstime.month, obstime.day, 12, 0, 0)

        args = dict(ra=self.ra * u.deg, dec=self.dec * u.deg, obstime=Time('J2000'), pm_ra_cosdec=self.rapm * MAS_YR, pm_dec=self.decpm * MAS_YR)

        if self.dist is not None:
            args['distance'] = self.dist * u.lightyear

        if self.rv is not None:
            args['radial_velocity'] = self.rv * u.km / u.second

        spos = SkyCoord(**args).apply_space_motion(new_obstime=Time(obstime))
        self.ra = spos.ra.deg
        self.dec = spos.dec.deg
        if self.dist is not None:
            self.dist = spos.distance.lightyear

    def load_position(self, node):
        """Load from XML DOM node"""
        self.dist = self.rv = self.ra = self.dec = self.rapm = self.decpm = self.origra = self.origdec = self.origdist = None
        for child in node:
            tagn = child.tag
            setattr(self, tagn, xmlutil.getfloat(child))
        if self.origra is None:
            self.origra = self.ra
        if self.origdec is None:
            self.origdec = self.dec
        if self.origdist is None:
            self.origdist = self.dist

    def save_position(self, doc, pnode, nodename="position"):
        """Save to XML DOM node"""
        if self.ra is None:
            return
        node = ET.SubElement(pnode, nodename)
        for name in ('ra', 'dec', 'dist', 'rv', 'rapm', 'decpm'):
            v = getattr(self, name, None)
            if v is not None:
                xmlutil.savedata(doc, node, name, v)
        if self.origra is not None and self.origra != self.ra:
            xmlutil.savedata(doc, node, "origra", self.origra)
        if self.origdec is not None and self.origdec != self.dec:
            xmlutil.savedata(doc, node, "origdec", self.origdec)
        if self.origdist is not None and self.origdist != self.dist:
            xmlutil.savedata(doc, node, "origdist", self.origdist)
