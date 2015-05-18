# Put everything for one spectrum set in a single XML file
# JMC 18/5/15 

import os.path
import string
import re
import xml.etree.ElementTree as ET

import miscutils
import xmlutil
import datarange

SPI_DOC_NAME = "SPECINFO"
SPI_DOC_ROOT = "specinfo"
CFILEELEM = "cfile"
RANGELIST = "rangelist"

class  SpecInfoError(Exception):
    """Class to report errors concerning spec info files"""
    pass

class  SpecInfo(object):
    """Details of spectum data including ranges"""
    
    def __init__(self):
        self.filename = None
        self.xmldoc = None
        self.xmlroot = None
        self.cfile = None
        self.rlist = None
        
    def loadfile(self, filename):
        """Load up a filename"""       
        try:
            self.xmldoc, self.xmlroot = xmlutil.load_file(filename, SPI_DOC_ROOT)
            self.filename = filename
        except xmlutil.XMLError as e:
            raise SpecInfoError(e.args[0])
    
    def get_ctrlfile(self):
        """Obtain control file list from XML doc
        Get a new one each time"""
        if self.xmlroot is None:
            raise SpecInfoError("No file loaded yet")
        
    
    def get_rangelist(self):
        """Obtain range list from XML doc
        Get a new one each time"""
    
    def set_ctrlfile(self, cfile):
        """Set control file list ready to save"""
    
    def set_rangelist(self, rlist):
        """Set range list ready to save"""
        
    
    def savefile(self, filename):
        """Save 