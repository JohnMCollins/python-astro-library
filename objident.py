"""Identification of an object"""

import xml.etree.ElementTree as ET
import xmlutil


class ObjIdentErr(Exception):
    """Class to raise if we have a problem with object idents"""

    def getmessage(self):
        """Get the message corresponding to the problem"""
        return " - no ".join(self.args)


class ObjIdent:
    """Contains name, display name and object index in database of known object"""

    ObjIdent_attr = ('dispname', 'vicinity', 'objind')
    ObjIdent_strings = ('objname', 'dispname', 'vicinity')

    def __init__(self, **kwargs):
        self.objname = self.dispname = self.vicinity = None
        self.objind = 0
        self.invented = False
        try:
            cobj = kwargs['copyobj']
            self.objname = cobj.objname
            self.invented = cobj.invented
            for n in ObjIdent.ObjIdent_attr:
                setattr(self, n, getattr(cobj, n))
        except (KeyError, AttributeError):
            pass
        try:
            self.objname = self.dispname = kwargs['name']
        except KeyError:
            pass
        for n in ObjIdent.ObjIdent_attr:
            try:
                setattr(self, n, kwargs[n])
            except KeyError:
                pass
        try:
            self.invented = kwargs['invented']
        except KeyError:
            pass

    def check_valid_id(self, check_dispname=True, check_vicinity=False, check_objind=False):
        """Indicate whether object is valid (has name and display name)"""
        if self.objname is None:
            raise ObjIdentErr("Invalid identifier", "Name")
        if check_dispname and self.dispname is None:
            raise ObjIdentErr("Invalid identifier", "Display name")
        if check_vicinity and self.vicinity is None:
            raise ObjIdentErr("Invalid identifier", "Vicinity")
        if check_objind and self.objind == 0:
            raise ObjIdentErr("Invalid identifier", "No object id")

    def fix_dispname(self):
        """Fix dispname to be the same as the object name if we haven't got it"""
        if self.dispname is None:
            self.dispname = self.objname

    def is_invented(self):
        """Report whether object has invented name"""
        return  self.invented

    def is_target(self):
        """Report if it's the target by comparing with vicinity"""
        return  self.objname is not None and self.objname == self.vicinity

    def set_invented(self, name, dispname=None):
        """Set an invented name for the object"""
        self.objname = self.dispname = name
        if dispname is not None:
            self.dispname = dispname
        self.invented = True

    def put_ident(self, dbcurs, fnames, fvalues):
        """Update lists of names and values for insertion into the database"""
        conn = dbcurs.connection
        for n in ObjIdent.ObjIdent_strings:
            val = getattr(self, n, None)
            if val is not None:
                fnames.append(n)
                fvalues.append(conn.escape(val))
        fnames.append('invented')
        if self.invented:
            fvalues.append('1')
        else:
            fvalues.append('0')

    def update_ident(self, dbcurs, fields):
        """Update fields vector to accommodate changes in ident"""
        conn = dbcurs.connection
        for n in ObjIdent.ObjIdent_strings:
            fields.append(n + "=" + conn.escape(getattr(self, n)))
        if self.invented:
            fields.append("invented=1")
        else:
            fields.append("invented=0")

    def load_ident(self, node):
        """Load from XML DOM node"""
        self.objname = self.dispname = self.vicinity = None
        self.objind = 0
        self.invented = xmlutil.getboolattr(node, "invented")
        for child in node:
            tagn = child.tag
            if tagn in ObjIdent.ObjIdent_strings:
                setattr(self, tagn, xmlutil.gettext(child))
            elif tagn == "objind":
                self.objind = xmlutil.getint(child)

        if self.dispname is None:
            self.dispname = self.objname

    def save_ident(self, doc, pnode, name="ident"):
        """Save to XML DOM node"""
        if self.objname is None:
            return
        node = ET.SubElement(pnode, name)
        xmlutil.setboolattr(node, "invented", self.invented)
        xmlutil.savedata(doc, node, "objname", self.objname)
        if self.dispname is not None and self.dispname != self.objname:
            xmlutil.savedata(doc, node, "dispname", self.dispname)
        if self.objind != 0:
            xmlutil.savedata(doc, node, "objind", self.objind)

        if self.vicinity is not None:
            xmlutil.savedata(doc, node, "vicinity", self.vicinity)
