# XML routines for object info database

import os.path
import string
import re
import xml.etree.ElementTree as ET
from astropy.time import Time
import datetime
import astropy.units as u
import miscutils
import xmlutil
import numpy as np
import math

SPI_DOC_NAME = "OBJINFO"
SPI_DOC_ROOT = "objinfo"

SUFFIX = 'objinf'

DEFAULT_APSIZE = 6

Time_origin = Time('J2000.0')
Time_now = Time(datetime.datetime.now())
Conv_pm = (u.mas/u.yr).to("deg/day")

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
        self.datebasis = 'J2000.0'
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

    def getvalue(self, tfrom = None):
        """Get RA or DEC value alone, adjusting for pm if set,
        in which case take time from parameter (datetime object) or now if not given"""
        if self.value is None:
            raise ObjDataError("RA/DEC value not defined")
        if self.pm is None:
            return  self.value
        et = Time_now
        if tfrom is not None:
            et = Time(tfrom)
        tdiff = et - Time_origin
        return self.value + self.pm * Conv_pm * tdiff.jd

class Name_Source(object):
    """Record name and source"""
    
    def __init__(self, objname = None, source = None):
        self.objname = objname
        self.source = source
    
    def load(self, node):
        """Load name value from node"""
        self.objname = xmlutil.gettext(node)
        try:
            self.source = node.attrib['source']
        except KeyError:
            self.source = None
    
    def save(self, doc, pnode, name):
        """Save mma,e amd source"""
        node = ET.SubElement(pnode, name)
        node.text = self.objname
        if self.source is not None:
            node.attrib['source'] = self.source

class Mag(object):
    """Represent a magnitude with filter"""
    
    def __init__(self, filter, val = None, err = None):
        self.value = val
        self.filter = filter
        self.err = err
    
    def load(self, node):
        """Load magnitude value from XML node"""
        self.value = None
        try:
            self.filter = node.attrib['filter']
        except KeyError:
            raise ObjDataError("Filter missing in mag data")
        self.err = None
        for child in node:
            tagn = child.tag
            if tagn == "value":
                self.value = xmlutil.getfloat(child)
            elif tagn == "err":
                self.err = xmlutil.getfloat(child)
    
    def save(self, doc, pnode, name):
        """Save magnitude data to file"""
        node = ET.SubElement(pnode, name)
        node.attrib['filter'] = self.filter
        xmlutil.savedata(doc, node, "value", self.value)
        if self.err is not None:
            xmlutil.savedata(doc, node, "err", self.err)

class Maglist(object):
    """Represents a list of magnitudes with various filters"""
    
    def __init__(self):
        self.maglist = dict()
    
    def is_def(self):
        """Return whether any mags defined"""
        return len(self.maglist) != 0
    
    def load(self, node):
        """Load a list of magnitudes from file"""
        self.maglist = []
        for child in node:
            nxt = Mag()
            nxt.load(child)
            self.maglist[nxt.filter] = nxt
    
    def save(self, doc, pnode, name):
        """Save a mag list to file"""
        node = ET.SubElement(pnode, name)
        for nxt in self.maglist.values():
            nxt.save(doc, node, "mag")
    
    def get_val(self, filter):
        """get magnitude for given filter"""
        try:
            mg = self.maglist[filter]
            return (mg.value, mg.err)
        except KeyError:
            raise ObjDataError("No magnitude defined for filter " + filter)
    
    def set_val(self, filter, value, err = None):
        """Set mag value"""
        self.msglist[filter] = Mag(filter, value, err)
    
    def av_val(self):
        """Return average value of magnitude and error as pair"""
        mags = []
        errs = []
        
        for nxt in self.maglist.values():
            mgs.append(nxt.value)
            errs.append(nxt.err)
        
        if len(mags) == 0:
            raise ObjDataError("No magnitudes assigned")
        
        m = np.mean(mags)
        if None in errs:
            e = None
        else:
            e = math.sqrt(np.mean(np.array(errs)**2))
        return (m, e)
        
class ObjData(object):
    """Decreipt an individaul object"""
    
    def __init__(self, objname = None, objtype = None, dist = None, rv = None, ra = None, dec = None):
        self.objname = objname
        self.dbnames = dict()
        self.objtype = objtype
        self.dist = dist
        self.rv = rv
        self.rightasc = RaDec(value = ra)
        self.decl = RaDec(value = dec)
        self.apsize = None
        self.maglist = Maglist()
    
    def set_alias(self, alias, source):
        """Add or update alias name DON'T USE if we are already in an ObjInfo structure"""
        newalias = Name_Source(alias, source)
        self.dbnames[alias] = newalias
    
    def del_alias(self, alias):
        """Delete alias name don't worry if not there DON'T USE if we are already in an ObjInfo structure"""
        try:
            del self.dbnames[alias]
        except KeyError:
            pass
    
    def list_aliases(self):
        """Give a list of aliases"""
        l = self.dbnames.values()
        l.sort(key=lambda x: x.objname)
        return l
    
    def list_alias_names(self):
        """Get a list of alias names without soucrces"""
        return sorted(self.dbnames.keys())
    
    def load(self, node):
        """Load object data from node"""
        self.objname = None
        self.dbnames = dict()
        self.objtype = None
        self.dist = None
        self.rv = None
        self.rightasc = None
        self.decl = None
        self.apsize = None
        self.maglist = Maglist()
        for child in node:
            tagn = child.tag
            if tagn == "name":
                self.objname = xmlutil.gettext(child)
            elif tagn == "dbnames":
                for dbc in child:
                    nxt = Name_Source()
                    nxt.load(dbc)
                    self.dbnames[nxt.objname] = nxt
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
            elif tagn == "apsize":
                self.apsize = xmlutil.getint(child)
            elif tagn == "mags":
                self.maglist.load(child)
    
    def save(self, doc, pnode, name):
        """Save object data tp node"""
        node = ET.SubElement(pnode, name)
        if self.objname is not None:
            xmlutil.savedata(doc, node, "name", self.objname)
        if len(self.dbnames) != 0:
            dnode = ET.SubElement(node, "dbnames")
            for dc in self.dbnames.values():
                dc.save(doc, dnode, "dbname")
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
        if self.apsize is not None:
            xmlutil.savedata(doc, node, "apsize", self.apsize)
        if self.maglist.is_def():
            self.maglist.save(doc, node, "maglist")
    
    def get_ra(self, tfrom = None):
        """Get RA value"""
        return  self.rightasc.getvalue(tfrom)
    
    def get_dec(self, tfrom = None):
        """Get DECL value"""
        return  self.decl.getvalue(tfrom)
    
    def set_ra(self, **kwargs):
        """Set RA value"""
        self.rightasc = RaDec(**kwargs)
        
    def set_dec(self, **kwargs):
        """Set RA value"""
        self.decl = RaDec(**kwargs)
        
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
    
    def get_aperture(self, defval = DEFAULT_APSIZE):
        """Retrun aperture size of object or default value"""
        if self.apsize is None:
            return defval
        return self.apsize
    
    def set_apsize(self, value):
        """Set aperture size"""
        self.apsize = value
    
    def get_mag(self, filter = None):
        """Get magnitude for given filter or average"""
        if filter is None:
            return self.maglist.av_val()
        return self.maglist.get_val(filter)
    
    def set_mag(self, filter, value, err = None):
        """Set magnitude for given filter"""
        self.maglist.set_val(filter, value, err)            
            
class  ObjInfoError(Exception):
    """Class to report errors concerning ob info files"""
    
    def __init__(self, message, warningonly = False):
        super(ObjInfoError, self).__init__(message)
        self.warningonly = warningonly

class  ObjInfo(object):
    """Details of object"""

    def __init__(self):
        self.filename = None
        self.xmldoc = None
        self.xmlroot = None
        self.objects = dict()
        self.alias2name = dict()
        self.allnames = dict()
        
    def has_file(self):
        """Return whether file name assigned"""
        return self.filename is not None

    def is_main(self, name):
        """Return whether name is a main name rather than alias"""
        return name in self.objects
    
    def is_alias(self, name):
        """Return whether name is an alias rather than a main name"""
        return name in self.alias2name
    
    def get_main(self, mainoralias):
        """Get the main name for the given name"""
        if self.is_main(mainoralias):
            return  mainoralias
        try:
            return  self.alias2name[mainoralias]
        except KeyError:
            raise ObjInfoError(mainoralias + " is an unknown name")
    
    def get_aliases(self, nameorobj):
        """Return aliases for name (or object)"""
        if type(nameorobj) is str:
            nameorobj = self.get_object(nameorobj)
        return nameorobj.list_aliases()
    
    def add_object(self, obj):
        """Add object to database"""
        objn = obj.objname
        if objn is None:
            raise ObjInfoError("No name in object to be added")
        if objn in self.objects:
            raise ObjInfoError("Object name " + objn + " clashes with existing object")
        if objn in self.allnames:
            raise ObjInfoError("Object name " + objn + " clashes w)th existing alias")
        for al in obj.list_alias_names():
            if al in self.allnames:
                raise ObjInfoError('Alias for ' + objn + ' of ' + al + ' clashes with exixting name')
        self.objects[objn] = obj
        self.allnames[objn] = obj
        for al in obj.list_alias_names():
            self.allnames[al] = obj
            self.alias2name[al] = objn

    def del_object(self, obj):
        """Delete object from database"""
        objn = obj.objname
        if objn is None:
            return
        try:
            del self.objects[objn]
        except KeyError:
            raise ObjInfoError("Object name " + objn + " not found")
        for al in obj.list_alias_names():
            del self.allnames[al]
            del self.alias2name[al]
    
    def is_defined(self, name):
        """Report whether defined"""
        return  name in self.allnames
    
    def get_object(self, name):
        """Get object as name or alias"""
        try:
            return self.allnames[name]
        except KeyError:
            raise ObjInfoError(name + ' is an unknown name')

    def add_aliases(self, main, source, *aliases):
        """Add one or more aliases to name"""
        try:
            if type(main) is str:
                main = self.objects[main]
        except KeyError:
            raise ObjInfoError(main + " is not in the list of objects")
        for alias in aliases:
            if alias in self.allnames:
                raise ObjInfoError(alias + " is already an alias name")
        for alias in aliases:
            main.set_alias(alias, source)
            self.allnames[alias] = main
            self.alias2name[alias] = main.objname

    def del_aliases(self, *aliases):
        """Remove one or more aliases"""
        for alias in aliases:
            if alias not in self.alias2name:
                raise ObjInfoError(alias + " is not an alias")
        for alias in aliases:
            mainobj = self.allnames[alias]
            del self.allnames[alias]
            del self.alias2name[alias]
            mainobj.del_alias(alias)
    
    def list_objects(self, tfrom = None):
        """list objects ordered by RA then DEC"""
        slist = []
        for a in self.objects.values():
            try:
                ra = a.get_ra(tfrom)
                dec = a.get_dec(tfrom)
            except ObjDataError:
                pass
            slist.append(a)
        slist.sort(key = lambda x: (x.get_ra(tfrom), x.get_dec(tfrom)))
        return  slist

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
                    self.allnames[ob.objname] = ob
                    for al in ob.list_alias_names():
                        self.allnames[al] = ob
                        self.alias2name[al] = ob.objname
        except xmlutil.XMLError as e:
            raise ObjInfoError(e.args[0], warningonly=e.warningonly)
    
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
            xmlutil.complete_save(outfile, self.xmldoc)
            self.filename = outfile
        except xmlutil.XMLError as e:
            raise ObjInfoError("Save file XML error - " + e.args[0])
