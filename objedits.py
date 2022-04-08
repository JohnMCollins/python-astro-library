"""Store interactive information about adjustments to objects"""

import re
import os.path
import xml.etree.ElementTree as ET
import xmlutil
import remdefaults
import objdata

EDITS_DOC_ROOT = "Edits1"

nmatch = re.compile("(.+)-(\d\d\d)+")


class ObjEditErr(Exception):
    """Raise if error found"""


class ObjEdit:
    """Base class for edit"""

    attr_list = dict(row=xmlutil.getint, col=xmlutil.getint, radeg=xmlutil.getfloat, decdeg=xmlutil.getfloat)

    def __init__(self, op, row, col):
        self.op = op
        self.done = False
        self.row = row
        self.col = col
        self.radeg = None
        self.decdeg = None

    def load(self, node):
        """Load from XML DOM node"""
        self.done = xmlutil.getboolattr(node, "done")
        for child in node:
            try:
                iproc = ObjEdit.attr_list[child.tag]
                setattr(self, child.tag, iproc(child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        node.set("op", self.op)
        if self.done:
            node.set("done", "y")
        for attr in ObjEdit.attr_list:
            v = getattr(self, attr, None)
            if v is not None:
                xmlutil.savedata(doc, node, attr, v)
        return node


class ObjEdit_Newobj_Base(ObjEdit):
    """Remember new objects"""

    attr_list = dict(name=xmlutil.gettext, dispname=xmlutil.gettext, adus=xmlutil.getfloat, newlabel=xmlutil.gettext)

    def __init__(self, op, row, col, name, dispname, radeg, decdeg):
        super().__init__(op, row, col)
        self.radeg = radeg
        self.decdeg = decdeg
        self.name = name
        self.dispname = dispname
        self.adus = None
        self.newlabel = None

    def load(self, node):
        """Load from XML DOM node"""
        super().load(node)
        for child in node:
            try:
                iproc = ObjEdit_Newobj_Base.attr_list[child.tag]
                setattr(self, child.tag, iproc(child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        "Save to XML DOM node"""
        node = super().save(doc, pnode, name)
        for attr in ObjEdit_Newobj_Base.attr_list:
            v = getattr(self, attr, None)
            if v is not None:
                xmlutil.savedata(doc, node, attr, v)
        return  node


class ObjEdit_Newobj_Ap(ObjEdit_Newobj_Base):
    """New object for when we are saving a given aperture"""

    def __init__(self, row=0, col=0, name="", dispname="", radeg=0.0, decdeg=0.0, apsize=0):
        super().__init__("create", row, col, name, dispname, radeg, decdeg)
        self.apsize = apsize

    def load(self, node):
        """Load from XML DOM node"""
        super().load(node)
        for child in node:
            if child.tag == "apsize":
                self.apsize = xmlutil.getint(child)
                break

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = super().save(doc, pnode, name)
        xmlutil.savedata(doc, node, "apsize", self.apsize)
        return  node


class ObjEdit_Newobj_Calcap(ObjEdit_Newobj_Base):
    """New object for when we are calculating an aperture"""

    def __init__(self, row=0, col=0, name="", dispname="", radeg=0.0, decdeg=0.0):
        super().__init__("createcalc", row, col, name, dispname, radeg, decdeg)


class ObjEdit_Exist_Base(ObjEdit):
    """Do something to an existing object"""

    attr_list = dict(objid=xmlutil.getint, oldlabel=xmlutil.gettext, newlabel=xmlutil.gettext)

    def __init__(self, op, oid, row, col, label):
        super().__init__(op, row, col)
        self.objid = oid
        self.oldlabel = label
        self.newlabel = None

    def load(self, node):
        """Load from XML DOM node"""
        super().load(node)
        for child in node:
            try:
                iproc = ObjEdit_Exist_Base.attr_list[child.tag]
                setattr(self, child.tag, iproc(child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        "Save to XML DOM node"""
        node = super().save(doc, pnode, name)
        for attr in ObjEdit_Exist_Base.attr_list:
            v = getattr(self, attr, None)
            if v is not None:
                xmlutil.savedata(doc, node, attr, v)
        return  node


class ObjEdit_Hide(ObjEdit_Exist_Base):
    """ For when we are hiding an object"""

    def __init__(self, oid=0, row=0, col=0, label=""):
        super().__init__("hide", oid, row, col, label)


class ObjEdit_Deldisp(ObjEdit_Exist_Base):
    """When we want to delete the display name of an object"""

    def __init__(self, oid=0, row=0, col=0, label=""):
        super().__init__("deldisp", oid, row, col, label)


class ObjEdit_Newdisp(ObjEdit_Exist_Base):
    """For when we are giving an object a new display name"""

    def __init__(self, oid=0, row=0, col=0, label="", dname=""):
        super().__init__("newdisp", oid, row, col, label)
        self.dispname = dname

    def load(self, node):
        """Load from XML DOM node"""
        super().load(node)
        for child in node:
            if child.tag == "dispname":
                self.dispname = xmlutil.gettext(child)
                break

    def save(self, doc, pnode, name):
        """Save to XML DOM Node"""
        node = super().save(doc, pnode, name)
        xmlutil.savedata(doc, node, "dispname", self.dispname)
        return  node


class ObjEdit_Adjap(ObjEdit_Exist_Base):
    """When we are adjusting aperture to given"""

    attr_list = dict(apsize=xmlutil.getint, adus=xmlutil.getfloat)

    def __init__(self, oid=0, row=0, col=0, label="", apsize=0):
        super().__init__("adjap", oid, row, col, label)
        self.apsize = apsize
        self.adus = None

    def load(self, node):
        """Load from XML DOM node"""
        super().load(node)
        for child in node:
            try:
                iproc = ObjEdit_Adjap.attr_list[child.tag]
                setattr(self, child.tag, iproc(child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        "Save to XML DOM node"""
        node = super().save(doc, pnode, name)
        for attr in ObjEdit_Adjap.attr_list:
            v = getattr(self, attr, None)
            if v is not None:
                xmlutil.savedata(doc, node, attr, v)
        return  node


class ObjEdit_Calcap(ObjEdit_Exist_Base):
    """For when we want to calculate the aperture"""

    def __init__(self, oid=0, row=0, col=0, label=""):
        super().__init__("calcap", oid, row, col, label)
        self.adus = None

    def load(self, node):
        """Load from XML DOM node"""
        super().load(node)
        for child in node:
            if child.tag == "adus":
                self.adus = xmlutil.getfloat(child)
                break

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = super().save(doc, pnode, name)
        if self.adus is not None:
            xmlutil.savedata(doc, node, "adus", self.adus)


class ObjEdit_List:
    """Class for editing list of object edits"""

    def __init__(self, vicinity):
        self.vicinity = vicinity
        self.editlist = []
        self.namelist = set()

    def load_findres(self, fr):
        """Load names from find_results"""
        for res in fr.results():
            if res.obj is not None:
                self.namelist.add(res.obj.objname)
                self.namelist.add(res.obj.dispname)
        for ed in self.editlist:
            if isinstance(ed, ObjEdit_Newobj_Base):
                self.namelist.add(ed.name)
                self.namelist.add(ed.dispname)

    def add_edit(self, edit):
        """Add edit to list"""
        self.editlist.append(edit)

    def nameok(self, dbase, name):
        """Check if name is OK and doesn't clash with anything"""
        return  not (objdata.nameused(dbase, name, True) or name in self.namelist)

    def getname(self, dbase, startname):
        """Get next name possibility"""
        if objdata.nameused(dbase, startname, True):
            startname = objdata.nextname(dbase, startname)
        if startname not in self.namelist:
            self.namelist.add(startname)
            return startname
        n = 0
        mtchs = nmatch.match(startname)
        if mtchs:
            startname, n = mtchs.groups()
            n = int(n)
        while 1:
            n += 1
            newname = "{:s}-{:03d}".format(startname, n)
            if self.nameok(dbase, newname):
                self.namelist.add(newname)
                return  newname

    def load(self, node):
        """Load from XML DOM node"""
        self.editlist = []
        for child in node:
            tagn = child.tag
            if tagn == "vicinity":
                self.vicinity = xmlutil.gettext(child)
            elif tagn == "editlist":
                for gc in child:
                    op = gc.get("op")
                    ed = None
                    if op == "create":
                        ed = ObjEdit_Newobj_Ap()
                    elif op == "createcalc":
                        ed = ObjEdit_Newobj_Calcap()
                    elif op == "hide":
                        ed = ObjEdit_Hide()
                    elif op == "deldisp":
                        ed = ObjEdit_Deldisp()
                    elif op == "newdisp":
                        ed = ObjEdit_Newdisp()
                    elif op == "adjap":
                        ed = ObjEdit_Adjap()
                    elif op == "calcap":
                        ed = ObjEdit_Calcap()
                    else:
                        continue
                    ed.load(gc)
                    self.editlist.append(ed)

    def save(self, doc, pnode):
        """Save to XML DOM node"""
        xmlutil.savedata(doc, pnode, "vicinity", self.vicinity)
        if len(self.editlist) != 0:
            lnode = ET.SubElement(pnode, "editlist")
            for ed in self.editlist:
                ed.save(doc, lnode, "edit")


def load_edits_from_file(fname, vicinity=None, create=True):
    """Load from edits file"""
    fname = remdefaults.edits_file(fname)
    result = ObjEdit_List(vicinity)

    if os.path.exists(fname):
        try:
            dummy, root = xmlutil.load_file(fname, EDITS_DOC_ROOT)
            result.load(root)
        except  xmlutil.XMLError as e:
            raise ObjEditErr("Load of " + fname + " gave " + e.args[0])
        if vicinity is not None and vicinity != result.vicinity:
            raise ObjEditErr("Vicinity in edits file " + fname + " of " + result.vicinity + " differs from supply of " + vicinity)
    elif not create:
        raise ObjEditErr("Edit file " + fname + " does not exist")
    elif vicinity is None:
        raise ObjEditErr("No vicinity given")
    return  result


def save_edits_to_file(edits, filename):
    """Save edits ub XNK file"""
    filename = remdefaults.edits_file(filename)
    try:
        doc, root = xmlutil.init_save(EDITS_DOC_ROOT, EDITS_DOC_ROOT)
        edits.save(doc, root)
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise ObjEditErr("Save of " + filename + " gave " + e.args[0])
