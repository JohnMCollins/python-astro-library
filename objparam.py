"""Information and notes about objects"""

import xml.etree.ElementTree as ET
import objinfo
import objident
import objposition
import objmags


class ObjParam(objident.ObjIdent, objinfo.ObjInfo, objposition.ObjPosition, objmags.ObjMags):
    """Merge of objecat data"""

    def __init__(self, **kwargs):
        objident.ObjIdent.__init__(self, **kwargs)
        objinfo.ObjInfo.__init__(self, **kwargs)
        objposition.ObjPosition.__init__(self, **kwargs)
        objmags.ObjMags.__init__(self, **kwargs)

    def put_param(self, dbcurs, fnames, fvalues):
        """Update lists of names and values for insertion into the database"""
        self.put_ident(dbcurs, fnames, fvalues)
        self.put_info(dbcurs, fnames, fvalues)
        self.put_position(fnames, fvalues)
        self.put_mags(fnames, fvalues)

    def update_param(self, dbcurs, fields):
        """Update fields vector to accommodate changes in info"""
        self.update_ident(dbcurs, fields)
        self.update_info(dbcurs, fields)
        self.update_position(fields)
        self.update_mags(fields)

    def load_param(self, node):
        """Load from XML DOM node"""
        for child in node:
            tagn = child.tag
            if tagn == "ident":
                self.load_ident(child)
            elif tagn == "info":
                self.load_info(child)
            elif tagn == "position":
                self.load_position(child)
            elif tagn == "mags":
                self.load_mags(child)

    def save_param(self, doc, pnode, name="objparam"):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        self.save_ident(doc, node)
        self.save_info(doc, node)
        self.save_position(doc, node)
        self.save_mags(doc, node)
        return  node
