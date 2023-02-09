"""Information and notes about objects"""

import xml.etree.ElementTree as ET
import xmlutil

DEFAULT_APSIZE = 6


class ObjInfo:
    """Information and notes about objects"""

    ObjInfo_attr = ('objtype', 'usable', 'apsize', 'irapsize', 'apstd', 'irapstd', 'basedon', 'irbasedon', 'variability')

    def __init__(self, **kwargs):
        self.objtype = None
        self.usable = True
        self.variability = 0.0
        self.apsize = self.irapsize = DEFAULT_APSIZE
        self.apstd = self.irapstd = None
        self.basedon = self.irbasedon = 0
        try:
            cobj = kwargs['copyobj']
            for n in ObjInfo.ObjInfo_attr:
                setattr(self, n, getattr(cobj, n))
        except (KeyError, AttributeError):
            pass
        for n in ObjInfo.ObjInfo_attr:
            if n in kwargs:
                setattr(self, n, kwargs[n])

    def put_info(self, dbcurs, fnames, fvalues):
        """Update lists of names and values for insertion into the database"""
        if self.objtype is not None and len(self.objtype) != 0:
            fnames.append("objtype")
            fvalues.append(dbcurs.connection.escape(self.objtype))
        fnames.append("usable")
        if self.usable:
            fvalues.append('1')
        else:
            fvalues.append('0')
        fnames.append("apsize")
        fvalues.append("{:.4g}".format(self.apsize))
        fnames.append("irapsize")
        fvalues.append("{:.4g}".format(self.irapsize))
        if self.apstd is not None:
            fnames.append("apstd")
            fvalues.append("{:.4e}".format(self.apstd))
        if self.irapstd is not None:
            fnames.append("irapstd")
            fvalues.append("{:.4e}".format(self.irapstd))
        if self.basedon is not None:
            fnames.append("basedon")
            fvalues.append("{:.d}".format(self.basedon))
        if self.irbasedon is not None:
            fnames.append("irbasedon")
            fvalues.append("{:.d}".format(self.irbasedon))
        fnames.append('variability')
        fvalues.append("{:.4f}".format(self.variability))

    def update_info(self, dbcurs, fields):
        """Update fields vector to accommodate changes in info"""
        if self.objtype is not None and len(self.objtype) != 0:
            fields.append("objtype=" + dbcurs.connection.escape(self.objtype))
        if self.usable:
            fields.append("usable=1")
        else:
            fields.append("usable=0")
        fields.append("apsize={:.4g}".format(self.apsize))
        fields.append("irapsize={:.4g}".format(self.irapsize))
        if self.apstd is not None:
            fields.append("apstd={:.4e}".format(self.apstd))
        if self.irapstd is not None:
            fields.append("irapstd={:.4e}".format(self.irapstd))
        if self.basedon is not None:
            fields.append("basedon={:d}".format(self.basedon))
        if self.irbasedon is not None:
            fields.append("irbasedon={:d}".format(self.irbasedon))
        fields.append("variability={:.4f}".format(self.variability))

    def load_info(self, node):
        """Load from XML DOM node"""
        self.objtype = None
        self.usable = not xmlutil.getboolattr(node, "unusable")
        self.apsize = self.irapsize = DEFAULT_APSIZE
        self.apstd = self.irapstd = None
        self.basedon = self.irbasedon = 0
        self.variability = 0.0
        for child in node:
            tagn = child.tag
            if tagn == "objtype":
                self.objtype = xmlutil.gettext(child)
            elif tagn == "apsize":
                self.apsize = xmlutil.getfloat(child)
            elif tagn == "irapsize":
                self.irapsize = xmlutil.getfloat(child)
            elif tagn == "apstd":
                self.apstd = xmlutil.getfloat(child)
            elif tagn == "irapstd":
                self.irapstd = xmlutil.getfloat(child)
            elif tagn == "basedon":
                self.basedon = xmlutil.getint(child)
            elif tagn == "irbasedon":
                self.irbasedon = xmlutil.getint(child)
            elif tagn == "variability":
                self.variability = xmlutil.getfloat(child)

    def save_info(self, doc, pnode, name="info"):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.objtype is not None and len(self.objtype) != 0:
            xmlutil.savedata(doc, node, "objtype", self.objtype)
        xmlutil.setboolattr(node, "unusable", not self.usable)
        xmlutil.savedata(doc, node, "apsize", self.apsize)
        xmlutil.savedata(doc, node, "irapsize", self.irapsize)
        if self.apstd is not None:
            xmlutil.savedata(doc, node, "apstd", self.apstd)
        if self.irapstd is not None:
            xmlutil.savedata(doc, node, "irapstd", self.irapstd)
        if self.basedon != 0:
            xmlutil.savedata(doc, node, "basedon", self.basedon)
        if self.irbasedon != 0:
            xmlutil.savedata(doc, node, "irbasedon", self.irbasedon)
        if self.variability != 0.0:
            xmlutil.savedata(doc, node, "variability", self.variability)
