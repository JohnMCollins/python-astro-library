# Save options in home control file for later recovery

import os
import sys
import string
import xml.etree.ElementTree as ET
import xmlutil
import configfile

class RemGeomError(Exception):
    """Throw in case of errors"""
    pass

class Trims(object):
    """Remember number of pixels to trim from each end of each frame"""
    
    def __init__(self):
        
        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0
    
    def load(self, node):
        """Load parameters from XML file"""
        
        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0
        
        for child in node:
            tagn = child.tag
            if tagn == "left":
                self.left = xmlutil.getint(child)
            elif tagn == "right":
                self.right = xmlutil.getint(child)
            elif tagn == "top":
                self.top = xmlutil.getint(child)
            elif tagn == "bottom":
                self.bottom = xmlutil.getint(child)
    
    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.left != 0:
            xmlutil.savedata(doc, node, "left", self.left)
        if self.right != 0:
            xmlutil.savedata(doc, node, "right", self.right)
        if self.top != 0:
            xmlutil.savedata(doc, node, "top", self.top)
        if self.bottom != 0:
            xmlutil.savedata(doc, node, "bottom", self.bottom)
  
class RemGeom(object):
    """Represent common parameters for Rem programs"""
    
    def __init__(self):
        self.trims = Trims()
        self.width = 10.0
        self.height = 12.0
    
    def load(self, node):
        """Load parameters from XML file"""
        
        self.trims = Trims()
        self.width = 10.0
        self.height = 12.0
        
        for child in node:
            tagn = child.tag
            if tagn == "trims":
                self.trims.load(child)
            elif tagn == "width":
                self.width = xmlutil.getfloat(child)
            elif tagn == "height":
                self.height = xmlutil.getfloat(child)
    
    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        self.trims.save(doc, node, "trims")
        xmlutil.savedata(doc, node, "width", self.width)
        xmlutil.savedata(doc, node, "height", self.height)

def load():
    """Load config geom from file"""
    ret = RemGeom()
    dr = configfile.load("remgeom", "REMGEOM")
    if dr is None:
        return ret
    (doc, root) = dr
    for child in root:
        if child.tag == "remg":
            ret.load(child)
    return ret

def save(rg):
    """Save config to file"""
    (doc, root) = configfile.init_save("REMGEOM")
    rg.save(doc, root, "remg")
    configfile.complete_save(doc, "remgeom")

