"""Aperture optimisation file/struct"""

import os.path
import xml.etree.ElementTree as ET
import xmlutil
import remdefaults

# import sys

APOPT_DOC_ROOT = "APopt"


class ApOptErr(Exception):
    """"Throw if error faound"""


class ApOpt:
    """Class for remembering an optimised aperture"""

    def __init__(self, apsize=0, objind=0, objname=None):
        self.apsize = apsize
        self.objind = objind
        self.objname = objname

    def load(self, node):
        """Load from XNK dom"""
        self.apsize = 0
        self.objind = 0
        self.objname = 0
        for child in node:
            tagn = child.tag
            if tagn == "apsize":
                self.apsize = xmlutil.getfloat(child)
            elif tagn == "objind":
                self.objind = xmlutil.getint(child)
            elif tagn == "objname":
                self.objname = xmlutil.gettext(child)

    def save(self, doc, pnode, name="optresult"):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "apsize", self.apsize)
        xmlutil.savedata(doc, node, "objind", self.objind)
        if self.objname is not None:
            xmlutil.savedata(doc, node, "objname", self.objname)


Fr_fields = dict(obsdate=xmlutil.getdatetime,
                 obsind=xmlutil.getint,
                 filter=xmlutil.gettext,
                 cutoff=xmlutil.getfloat)


class ApOptResults:
    """A class for remembering things we've found"""

    def __init__(self):
        self.resultlist = []
        self.obsdate = None
        self.obsind = None
        self.filter = None
        self.cutoff = None

    def load(self, node):
        """Load up from XML dom"""

        self.obsdate = None
        self.obsind = None
        self.filter = None
        self.cutoff = None
        self.resultlist = []

        for child in node:
            tagn = child.tag
            try:
                setattr(self, tagn, Fr_fields[tagn](child))
            except KeyError:
                if tagn == "results":
                    for gc in child:
                        fr = ApOpt()
                        fr.load(gc)
                        self.resultlist.append(fr)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        for k in Fr_fields:
            v = getattr(self, k, None)
            if v is not None:
                xmlutil.savedata(doc, node, k, v)
        if len(self.resultlist) != 0:
            gc = ET.SubElement(node, "results")
            for fr in self.resultlist:
                fr.save(doc, gc)


def load_apopts_from_file(fname):
    """Load results from results text file"""
    fname = remdefaults.apopt_file(fname)
    try:
        dummy, root = xmlutil.load_file(fname, APOPT_DOC_ROOT)
        fr = ApOptResults()
        frnode = root.find("RES")
        if frnode is None:
            raise xmlutil.XMLError("No tree")
        fr.load(frnode)
    except xmlutil.XMLError as e:
        raise ApOptErr("Load of " + fname + " gave " + e.args[0])
    return  fr


def save_apopts_to_file(results, filename, force=False):
    """Save results to results text file"""
    filename = remdefaults.apopt_file(filename)
    if not force and os.path.exists(filename):
        raise ApOptErr("Will not overwrite existing file " + filename)
    try:
        doc, root = xmlutil.init_save(APOPT_DOC_ROOT, APOPT_DOC_ROOT)
        results.save(doc, root, "RES")
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise ApOptErr("Save of " + filename + " gave " + e.args[0])
