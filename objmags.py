"""Identification of an object"""

import xml.etree.ElementTree as ET
import xmlutil

Possible_filters = 'girzHJK'
Possible_types = ("mag", "bri", "brisd")
Database_fields = []
for pf in Possible_filters:
    for pt in Possible_types:
        Database_fields.append(pf + pt)
Joined_fields = ','.join(Database_fields)


class ObjMagError(Exception):
    """Throw me if we get some error"""


class ObjMags:
    """Contains observed brightnesses etc of objects"""

    def __init__(self, **kwargs):
        for f in Database_fields:
            setattr(self, f, None)
        try:
            cobj = kwargs['copyobj']
            for n in Database_fields:
                setattr(self, n, getattr(cobj, n))
        except (KeyError, AttributeError):
            pass

    def get_mags(self, dbcurs, objind):
        """Fetch magnitude parameters from database corresponding to object"""
        if dbcurs.execute("SELECT " + Joined_fields + " FROM objdata WHERE ind={:d}".format(objind)) != 1:
            raise ObjMagError("Cannot get magnitudes for objind {:d}".format(objind))
        r = dbcurs.fetchall()
        for f, v in zip(Database_fields, r[0]):
            setattr(self, f, v)

    def put_mags(self, fnames, fvalues):
        """Update field names and values lists for inclusion in INSERT statement"""
        for f in Database_fields:
            try:
                fvalues.append("{:.6e}".format(getattr(self, f)))
                fnames.append(f)  # Did that second in case value gives exception
            except AttributeError:
                pass

    def update_mags(self, fields):
        """Update fields vector for inclusion in UPDATE statement"""
        for f in Database_fields:
            try:
                fields.append("{:s}={:.6e}".format(f, getattr(self, f)))
            except AttributeError:
                pass

    def load_mags(self, node):
        """Load from XML DOM node"""
        for f in Database_fields:
            setattr(self, f, None)
        for child in node:
            setattr(self, child.tag, xmlutil.getfloat(child))

    def save_mags(self, doc, pnode, name="mags"):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        for f in Database_fields:
            val = getattr(self, f, None)
            if val is not None:
                xmlutil.savedata(doc, node, f, val)
