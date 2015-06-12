# Put everything for one spectrum set in a single XML file
# JMC 18/5/15

import os.path
import string
import re
import xml.etree.ElementTree as ET

import miscutils
import xmlutil
import datarange
import specdatactrl

SPI_DOC_NAME = "SPECINFO"
SPI_DOC_ROOT = "specinfo"
CFILEELEM = "cfile"
RANGELIST = "rangelist"

SUFFIX = 'spi'

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

    def is_complete(self):
        """Check we have file OK to reload from"""
        return self.cfile is not None and self.rlist is not None

    def has_file(self):
        return self.filename is not None

    def loadfile(self, filename):
        """Load up a filename"""
        try:
            self.xmldoc, self.xmlroot = xmlutil.load_file(filename, SPI_DOC_ROOT)
            self.filename = filename
            self.get_ctrlfile()
            self.get_rangelist()
        except xmlutil.XMLError as e:
            raise SpecInfoError(e.args[0])

    def get_ctrlfile(self, refresh=False):
        """Obtain control file list from XML doc
        Get a new one if refresh given"""
        if not refresh and self.cfile is not None: return self.cfile
        if self.xmlroot is None:
            raise SpecInfoError("No file loaded yet")
        try:
            newlist = specdatactrl.SpecDataList(self.filename)
            cnode = xmlutil.find_child(self.xmlroot, CFILEELEM)
            newlist.load(cnode)
            self.cfile = newlist
        except xmlutil.XMLError as e:
            raise SpecInfoError("Load control file XML error: " + e.args[0])
        return self.cfile

    def get_rangelist(self, refresh=False):
        """Obtain range list from XML doc
        Get a new one if refresh given"""
        if not refresh and self.rlist is not None: return self.rlist
        if self.xmlroot is None:
            raise SpecInfoError("No file loaded yet")
        try:
            newrl = datarange.RangeList()
            rlnode = xmlutil.find_child(self.xmlroot, RANGELIST)
            newrl.load(rlnode)
            self.rlist = newrl
        except xmlutil.XMLError as e:
            raise SpecInfoError("Saved range error - " + e.args[0])
        return self.rlist

    def set_ctrlfile(self, cfile):
        """Set control file list ready to save"""
        if not isinstance(cfile, specdatactrl.SpecDataList):
            raise SpecInfoError("Set_ctrl file invalid argument")
        self.cfile = cfile

    def set_rangelist(self, rlist):
        """Set range list ready to save"""
        if not isinstance(rlist, datarange.RangeList):
            raise SpecInfoError("Set_range list invalid argument")
        self.rlist = rlist

    def savefile(self, filename = None):
        """Save stuff to file"""
        outfile = self.filename
        if filename is not None: outfile = filename
        if outfile is None:
            raise SpecInfoError("No out file given")
        if self.cfile is None:
            raise SpecInfoError("No control file set to save")
        if self.rlist is None:
            raise SpecInfoError("No range list set to save")
        try:
            self.xmldoc, self.xmlroot = xmlutil.init_save(SPI_DOC_NAME, SPI_DOC_ROOT)
            self.rlist.save(self.xmldoc, self.xmlroot, RANGELIST)
            self.cfile.save(self.xmldoc, self.xmlroot, CFILEELEM)
            xmlutil.complete_save(outfile, self.xmldoc)
            self.filename = outfile
        except xmlutil.XMLError as e:
            raise SpecInfoError("Save file XML error - " + e.args[0])
        except datarange.DataRangeError as e:
            raise SpecInfoError("Save range list error - " + e.args[0])
        except specdatactrl.SpecDataError as e:
            raise SpecInfoError("Save ctrl file error - " + e.args[0])
