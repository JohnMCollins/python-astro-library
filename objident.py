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

    ObjIdent_attr = ('dispname', 'latexname', 'vicinity', 'objind', 'label')
    ObjIdent_strings = ('objname', 'dispname', 'latexname', 'vicinity')

    def __init__(self, **kwargs):
        self.objname = self.dispname = self.latexname = self.vicinity = self.label = None
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

    def valid_label(self):
        """Report if object has valid label - uppercase letter"""
        return  self.label is not None and self.label.isupper()

    def fix_dispname(self):
        """Fix dispname to be the same as the object name if we haven't got it"""
        if self.dispname is None:
            self.dispname = self.objname
        if self.latexname is None:
            self.latexname = self.dispname

    def is_invented(self):
        """Report whether object has invented name"""
        return  self.invented

    def is_target(self):
        """Report if it's the target by comparing with vicinity"""
        return  self.objname is not None and self.objname == self.vicinity

    def set_invented(self, name, dispname=None, latexname=None):
        """Set an invented name for the object"""
        self.objname = self.dispname = self.latexname = name
        if dispname is not None:
            self.dispname = dispname
        if latexname is not None:
            self.latexname = latexname
        self.invented = True

    def put_ident(self, dbcurs, fnames, fvalues):
        """Update lists of names and values for insertion into the database"""
        conn = dbcurs.connection
        for n in ObjIdent.ObjIdent_strings:
            val = getattr(self, n, None)
            if val is not None:
                fnames.append(n)
                fvalues.append(conn.escape(val))
        if self.valid_label():
            fnames.append("label")
            fvalues.append(conn.escape(self.label))
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
        if self.valid_label():
            fields.append("label="+conn.escape(self.label))
        else:
            fields.append("label=NULL")
        if self.invented:
            fields.append("invented=1")
        else:
            fields.append("invented=0")

    def load_ident(self, node):
        """Load from XML DOM node"""
        self.objname = self.dispname = self.latexname = self.vicinity = self.label = None
        self.objind = 0
        self.invented = xmlutil.getboolattr(node, "invented")
        for child in node:
            tagn = child.tag
            if tagn in ObjIdent.ObjIdent_strings + ("label",):
                setattr(self, tagn, xmlutil.gettext(child))
            elif tagn == "objind":
                self.objind = xmlutil.getint(child)

        if self.dispname is None:
            self.dispname = self.objname
        if self.latexname is None:
            self.latexname = self.dispname

    def save_ident(self, doc, pnode, name="ident"):
        """Save to XML DOM node"""
        if self.objname is None:
            return
        node = ET.SubElement(pnode, name)
        xmlutil.setboolattr(node, "invented", self.invented)
        xmlutil.savedata(doc, node, "objname", self.objname)
        if self.dispname is not None and self.dispname != self.objname:
            xmlutil.savedata(doc, node, "dispname", self.dispname)
        if self.latexname is not None and self.latexname != self.dispname:
            xmlutil.savedata(doc, node, "latexname", self.latexname)
        if self.objind != 0:
            xmlutil.savedata(doc, node, "objind", self.objind)

        if self.vicinity is not None:
            xmlutil.savedata(doc, node, "vicinity", self.vicinity)
        if self.valid_label():
            xmlutil.savedata(doc, node, "label", self.label)
