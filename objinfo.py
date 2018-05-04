# XML routines for object info database

import os.path
import string
import re
import xml.etree.ElementTree as ET

import miscutils
import xmlutil

SPI_DOC_NAME = "OBJINFO"
SPI_DOC_ROOT = "objinfo"

SUFFIX = 'objinf'

class  ObjDataError(Exception):
    """Class to report errors concerning individual objects"""
    pass

class RaDec(object):
    """Class to store RA and Dec in providing for PM and uncertainties
    
    Always store as degrees [0,360) for RA and [-90,90] for DEC
    PM stored as MAS / yr"""
    
    def __init__(self, value = None, err = None, pm = None, datebasis = 'J2000.0'):
        self.value = value
        self.err = err
        self.pm = pm
        self.datebasis = datebasis
    
    def load(self, node):
        """Load RA or DEC value from node"""
        self.value = None
        self.err = None
        self.pm = None
        self.datebasis = None
        for child in node:
            tagn = child.tag
            if tagn == "value":
                self.value = xmlutil.getfloat(child)
            elif tagn == "err":
                self.err = xmlutil.getfloat(child)
            elif tagn == "pm":
                self.pm = xmlutil.getfloat(child)
            elif tagn == "basis":
                self.datebasis = xmlutil.gettext(child)
    
    def save(self, doc, pnode, name):
        """Save RA or DEC value from node"""
        if self.value is None: return
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "value", self.value)
        if self.err is not None:
            xmlutil.savedata(doc, node, "err", self.err)
        if self.pm is not None:
            xmlutil.savedata(doc, node, "pm", self.pm)
        if self.datebasis is not None and self.datebasis != 'J2000.0':
            xmlutil.savedata(doc, node, "basis", self.datebasis)

    def getvalue(self):
        """Get RA or DEC value alone"""
        if self.value is None:
            raise ObjDataError("RA/DEC value not defined")
        return  self.value
        
class ObjData(object):
    """Decreipt an individaul object"""
    
    def __init__(self, objname = None, sbname = None, objtype = None, dist = None, rv = None, ra = None, dec = None, mag = None):
        self.objname = objname
        self.sbname = sbname
        self.objtype = objtype
        self.dist = dist
        self.rv = rv
        self.rightasc = RaDec(value = ra)
        self.decl = RaDec(value = dec)
        self.mag = mag
        self.magerr = None
    
    def load(self, node):
        """Load object data from node"""
        self.objname = None
        self.sbname = None
        self.objtype = None
        self.dist = None
        self.rv = None
        self.rightasc = None
        self.decl = None
        self.mag = None
        self.magerr = None
        for child in node:
            tagn = child.tag
            if tagn == "name":
                self.objname = xmlutil.gettext(child)
            elif tagn == "sbname":
                self.sbname = xmlutil.gettext(child)
            elif tagn == "type":
                self.objtype = xmlutil.gettext(child)
            elif tagn == "dist":
                self.dist = xmlutil.getfloat(child)
            elif tagn == "rv":
                self.rv = xmlutil.getfloat(child)
            elif tagn == "ra":
                self.rightasc = RaDec()
                self.rightasc.load(child)
            elif tagn == "decl":
                self.decl = RaDec()
                self.decl.load(child)
            elif tagn == "mag":
                self.mag = xmlutil.getfloat(child)
            elif tagn == "magerr":
                self.magerr = xmlutil.getfloat(child)
    
    def save(self, doc, pnode, name):
        """Save object data tp node"""
        node = ET.SubElement(pnode, name)
        if self.objname is not None:
            xmlutil.savedata(doc, node, "name", self.objname)
        if self.objname is not None:
            xmlutil.savedata(doc, node, "sbname", self.sbname)
        if self.objtype is not None:
            xmlutil.savedata(doc, node, "type", self.objtype)
        if self.dist is not None:
            xmlutil.savedata(doc, node, "dist", self.dist)
        if self.rv is not None:
            xmlutil.savedata(doc, node, "rv", self.rv)
        if self.rightasc is not None:
            self.rightasc.save(doc, node, "ra")
        if self.decl is not None:
            self.decl.save(doc, node, "decl")
        if self.mag is not None:
            xmlutil.savedata(doc, node, "mag", self.mag)
        if self.magerr is not None:
            xmlutil.savedata(doc, node, "magerr", self.magerr)
    
    def get_ra(self):
        """Get RA value"""
        return  self.rightasc.getvalue()
    
    def get_dec(self):
        """Get DECL value"""
        return  self.decl.getvalue()
    
    def set_ra(self, **kwargs):
        """Set RA value"""
        self.rightasc = RaDec(kwargs)
        
    def set_dec(self, **kwargs):
        """Set RA value"""
        self.decl = RaDec(kwargs)
        
    def update_ra(self, value = None, err = None, pm = None, datebasis = None):
        """Update RA value"""
        if value is not None:
            self.rightasc.value = value
        if err is not None:
            self.rightasc.err = value
        if pm is not None:
            self.rightasc.pm = value
        if datebasis is not None:
            self.rightasc.datebasis = value
        
    def update_dec(self, value = None, err = None, pm = None, datebasis = None):
        """Update DECL value"""
        if value is not None:
            self.decl.value = value
        if err is not None:
            self.decl.err = value
        if pm is not None:
            self.decl.pm = value
        if datebasis is not None:
            self.decl.datebasis = value
            
class  ObjInfoError(Exception):
    """Class to report errors concerning ob info files"""
    pass

class  ObjInfo(object):
    """Details of object"""

    def __init__(self):
        self.filename = None
        self.xmldoc = None
        self.xmlroot = None
        self.objects = dict()
        self.alias2name = dict()
        self.name2alias = dict()
        self.sbnames = dict()
               
    def has_file(self):
        return self.filename is not None
    
    def add_object(self, obj):
        """Add object to database"""
        objn = obj.objname
        if objn is None:
            raise ObjInfoError("No name in object to be added")
        if objn in self.objects:
            raise ObjInfoError("Object name " + objn + " clashes with existing object")
        if objn in self.alias2name:
            raise ObjInfoError("Object name " + objn + " clashes w)th existing alias")
        self.objects[objn] = obj
        if obj.sbname is not None:
            self.sbnames[obj.sbname] = obj
    
    def del_object(self, obj):
        """Delete object from database"""
        objn - obj.objname
        if objn is None:
            return
        try:
            del self.objects[objn]
        except KeyError:
            raise ObjInfoError("Object name " + objn + " not found")
        for k, v in dict(self.alias2name).items():
            if v == objn:
                del self.alias2name[k]
        if obj.sbname is not None:
            del self.sbnames[obj.sbname]
    
    def is_defined(self, name):
        """Report whether defined"""
        return  name in self.objects or name in self.alias2name or name in self.sbnames
    
    def get_object(self, name):
        """Get object as name or alias"""
        try:
            return self.objects[name]
        except KeyError:
            pass
        try:
            main = self.alias2name[name]
            return self.objects[main]
        except KeyError:
            pass
        try:
            return self.sbnames[name]
        except KeyError:
            raise ObjInfoError(name + ' is an unknown name"')

    def add_aliases(self, main, *aliases):
        """Add one or more aliases to name"""
        if main not in self.objects:
            raise ObjInfoError(main + " is not in the list of objects")
        for alias in aliases:
            if alias in self.objects:
                raise ObjInfoError(alias + " is already a main object name")
            if alias in self.alias2name:
                raise ObjInfoError(alias + " is already an alias for " + self.alias2name[alias])
        for alias in aliases:
            self.alias2name[alias] = main
            if main in self.name2alias:
                self.name2alias[main].append(alias)
            else:
                self.name2alias[main] = [alias]

    def del_aliases(self, *aliases):
        """Remove one or more aliases"""
        for alias in aliases:
            if alias not in self.alias2name:
                raise ObjInfoError(alias + " is not an alias")
        for alias in aliases:
            main = self.alias2name[alias]
            del self.alias2name[alias]
            self.name2alias[main].remove(alias)
            if len(self.name2alias[main]) == 0:
                del self.name2alias[main]

    def loadfile(self, filename):
        """Load up a filename"""
        filename = miscutils.addsuffix(filename, SUFFIX)
        try:
            self.xmldoc, self.xmlroot = xmlutil.load_file(filename, SPI_DOC_ROOT)
            self.filename = filename
            obs = self.xmlroot.find("objects")
            if obs is not None:
                for obn in obs:
                    ob = ObjData()
                    ob.load(obn)
                    self.objects[ob.objname] = ob
                    if ob.sbname is not None:
                        self.sbnames[ob.sbname] = ob
            als = self.xmlroot.find('aliases')
            if als is not None:
                for aln in als:
                    alist = []
                    alname = aln.attrib['name']
                    for alcn in aln:
                        afrom = alcn.text
                        alist.append(afrom)
                        self.alias2name[afrom] = alname
                    self.name2alias[alname] = alist

        except xmlutil.XMLError as e:
            raise ObjInfoError(e.args[0])
    
    def savefile(self, filename = None):
        """Save stuff to file"""
        outfile = self.filename
        if filename is not None: outfile = miscutils.addsuffix(filename, SUFFIX)
        if outfile is None:
            raise ObjInfoError("No out file given")
        try:
            self.xmldoc, self.xmlroot = xmlutil.init_save(SPI_DOC_NAME, SPI_DOC_ROOT)
            obs = ET.SubElement(self.xmlroot, 'objects')
            for obj in self.objects.values():
                obj.save(self.xmldoc, obs, 'object')
            als = ET.SubElement(self.xmlroot, "aliases")
            for alname in self.name2alias:
                asn = ET.SubElement(als, "alias")
                asn.attrib['name'] = alname
                for afrom in self.name2alias[alname]:
                    af = ET.SubElement(asn, "af")
                    af.text = afrom
            xmlutil.complete_save(outfile, self.xmldoc)
            self.filename = outfile
        except xmlutil.XMLError as e:
            raise ObjInfoError("Save file XML error - " + e.args[0])
