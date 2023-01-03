"""Identification of an object"""

import xml.etree.ElementTree as ET
import xmlutil

class ObjPositionErr(Exception):
    """Class to raise if we have a problem with object positions"""

    def getmessage(self):
        """Get the message corresponding to the problem"""
        return " - no ".join(self.args)

class ObjPosition:
    """Contains name, display name and object index in database of known object"""

    ObjPosition_attr = ('rv', 'ra', 'dec', 'dist', 'rapm', 'decpm')

    def __init__(self, **kwargs):
        self.dist = self.rv = self.ra = self.dec = self.rapm = self.decpm = None
        self.timebasedon = None
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

    def put_position(self, fnames, fvalues):
        """Update lists of names and values for insertion into the database"""
        for name, val in (('radeg', self.ra), ('decdeg', self.dec), ('rv', self.rv), ('dist', self.dist), ('rapm', self.rapm), ('decpm', self.decpm)):
            if val is not None:
                fnames.append(name)
                fvalues.apppend("{:.9e}".format(val))

    def update_position(self, fields):
        """Update fields vector to accommodate changes in position info"""
        for name, val in (('radeg', self.ra), ('decdeg', self.dec), ('rv', self.rv), ('dist', self.dist), ('rapm', self.rapm), ('decpm', self.decpm)):
            if val is not None:
                fields.append("{:s}={:.9e}".format(name, val))

    def in_region(self, minra, maxra, mindec, maxdec):
        """Check if object is in region"""
        return  minra <= self.ra <= maxra and mindec <= self.dec <= maxdec

    def load_position(self, node):
        """Load from XML DOM node"""
        self.dist = self.rv = self.ra = self.dec = self.rapm = self.decpm = None
        for child in node:
            tagn = child.tag
            setattr(self, tagn, xmlutil.getfloat(child))

    def save_position(self, doc, pnode, nodename="position"):
        """Save to XML DOM node"""
        if self.ra is None:
            return
        node = ET.SubElement(pnode, nodename)
        for name in ('ra', 'dec', 'dist', 'rv', 'rapm', 'decpm'):
            v = getattr(self, name, None)
            if v is not None:
                xmlutil.savedata(doc, node, name, v)
