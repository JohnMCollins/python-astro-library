# Save options in home control file for later recovery

import os
import sys
import string
import xml.etree.ElementTree as ET
import xmlutil
import configfile
import matplotlib.pyplot as plt


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

    def apply_wcs(self, wcsc):
        """Set coords according to trims"""

        if wcsc is None:
            return
        wcsc.set_offsets(yoffset=self.bottom, xoffset=self.left)

    def apply_image(self, arr):
        """Apply trims to array"""
        if self.bottom != 0:
            arr = arr[self.bottom:]
        if self.top != 0:
            arr = arr[0:-self.top]
        if self.left != 0:
            arr = arr[:, self.left:]
        if self.right != 0:
            arr = arr[:, 0:-self.right]
        return arr

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


class Divspec(object):
    """Preferences for division display"""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        """Initialise default values"""
        self.nocoords = False
        self.invertim = True
        self.divisions = 8
        self.divprec = 3
        self.divthresh = 15
        self.racol = "#771111"
        self.deccol = "#771111"
        self.divalpha = 0.5

    def load(self, node):
        """Load parameters from XML file"""

        self.set_defaults()
        self.invertim = False

        for child in node:
            tagn = child.tag
            if tagn == "nocoords":
                self.nocoords = True
            elif tagn == "invertim":
                self.invertim = True
            elif tagn == "divisions":
                self.divisions = xmlutil.getint(child)
            elif tagn == "divprec":
                self.divprec = xmlutil.getint(child)
            elif tagn == "divthresh":
                self.divthresh = xmlutil.getint(child)
            elif tagn == "racol":
                self.racol = xmlutil.gettext(child)
            elif tagn == "deccol":
                self.deccol = xmlutil.gettext(child)
            elif tagn == "divalpha":
                self.divalpha = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to xml DOM node"""
        node = ET.SubElement(pnode, name)
        if self.nocoords:
            ET.SubElement(node, "nocoords")
        if self.invertim:
            ET.SubElement(node, "invertim")
        xmlutil.savedata(doc, node, "divisions", self.divisions)
        xmlutil.savedata(doc, node, "divprec", self.divprec)
        xmlutil.savedata(doc, node, "divthresh", self.divthresh)
        xmlutil.savedata(doc, node, "racol", self.racol)
        xmlutil.savedata(doc, node, "deccol", self.deccol)
        xmlutil.savedata(doc, node, "divalpha", self.divalpha)


class Objdisp(object):
    """Specify how objects are highlighted"""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        """Initialise to default values"""
        self.objcolour = ["cyan" ]
        self.objalpha = 1.0
        self.objtextfs = 12
        self.objtextdisp = 30
        self.objfill = False

    def load(self, node):
        """Load from XML DOM tree"""
        self.set_defaults()
        for child in node:
            tagn = child.tag
            if tagn == "objcolour":
                self.objcolour = xmlutil.gettext(child).split(':')
            elif tagn == "objalpha":
                self.objalpha = xmlutil.getfloat(child)
            elif tagn == "objtextfs":
                self.objtextfs = xmlutil.getint(child)
            elif tagn == "objtextdisp":
                self.objtextdisp = xmlutil.getint(child)
            elif tagn == "objfill":
                self.objfill = True

    def save(self, doc, pnode, name):
        """Save to xml DOM node"""
        node = ET.SubElement(pnode, name)
        if self.objfill:
            ET.SubElement(node, "objfill")
        xmlutil.savedata(doc, node, "objcolour", ":".join(self.objcolour))
        xmlutil.savedata(doc, node, "objalpha", self.objalpha)
        xmlutil.savedata(doc, node, "objtextfs", self.objtextfs)
        xmlutil.savedata(doc, node, "objtextdisp", self.objtextdisp)


class Winfmt(object):
    """Label format stuff for display"""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        """Initialise to default values"""
        self.width = 10.0
        self.height = 12.0
        self.labsize = 10
        self.ticksize = 10

    def load(self, node):
        """Load from XML DOM tree"""
        self.set_defaults()
        for child in node:
            tagn = child.tag
            if tagn == "labsize":
                self.labsize = xmlutil.getint(child)
            elif tagn == "ticksize":
                self.ticksize = xmlutil.getint(child)
            elif tagn == "width":
                self.width = xmlutil.getfloat(child)
            elif tagn == "height":
                self.height = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to xml DOM node"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "labsize", self.labsize)
        xmlutil.savedata(doc, node, "ticksize", self.ticksize)
        xmlutil.savedata(doc, node, "width", self.width)
        xmlutil.savedata(doc, node, "height", self.height)


class RemGeom(object):
    """Represent common parameters for Rem programs"""

    def __init__(self):
        self.trims = Trims()
        self.divspec = Divspec()
        self.objdisp = Objdisp()
        self.defwinfmt = Winfmt()
        self.altfmts = dict()

    def load(self, node):
        """Load parameters from XML file"""

        self.trims = Trims()
        self.divspec = Divspec()
        self.defwinfmt = Winfmt()
        self.altfmts = dict()

        for child in node:
            tagn = child.tag
            if tagn == "trims":
                self.trims.load(child)
            elif tagn == "divspec":
                self.divspec.load(child)
            elif tagn == "objdisp":
                self.objdisp.load(child)
            elif tagn == "labfmt":  # Cope with old version
                savewidth = self.defwinfmt.width
                saveheight = self.defwinfmt.height
                self.defwinfmt.load(child)
                self.defwinfmt.width = savewidth
                self.defwinfmt.height = saveheight
            elif tagn == "defwinfmt":
                self.defwinfmt.load(child)
            elif tagn == "altfmts":
                for gc in child:
                    newf = Winfmt()
                    newf.load(gc)
                    self.altfmts[gc.tag] = newf
            elif tagn == "width":  # Cope with old version
                self.defwinfmt.width = xmlutil.getfloat(child)
            elif tagn == "height":  # Cope with old version
                self.defwinfmt.height = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        self.trims.save(doc, node, "trims")
        self.divspec.save(doc, node, "divspec")
        self.objdisp.save(doc, node, "objdisp")
        self.defwinfmt.save(doc, node, "defwinfmt")
        if len(self.altfmts) != 0:
            afn = ET.SubElement(node, "altfmts")
            for k, v in self.altfmts.items():
                v.save(doc, afn, k)

    def disp_argparse(self, argp, fmt=None):
        """Initialise arg parser with display options"""
        which = self.defwinfmt
        if fmt is not None and fmt in self.altfmts:
            which = self.altfmts[fmt]
        argp.add_argument('--width', type=float, default=which.width, help="Width of figure")
        argp.add_argument('--height', type=float, default=which.height, help="Height of figure")
        argp.add_argument('--labsize', type=int, default=which.labsize, help='Label and title font size')
        argp.add_argument('--ticksize', type=int, default=which.ticksize, help='Tick font size')

    def disp_getargs(self, resargs):
        """Get arguments and reset parameters

        BN overwirtes defaults"""

        try:
            self.defwinfmt.width = resargs['width']
            self.defwinfmt.height = resargs['height']
            self.defwinfmt.labsize = resargs['labsize']
            self.defwinfmt.ticksize = resargs['ticksize']
        except KeyError as e:
            print("Error in parsed arguments", e.args[0], "is missing", file=sys.stderr)

    def plt_figure(self):
        """Create plot figure and return it. Initialise tick size"""
        plotfigure = plt.figure(figsize=(self.defwinfmt.width, self.defwinfmt.height))
        plt.rc("font", size=self.defwinfmt.labsize)
        plt.rc('xtick', labelsize=self.defwinfmt.ticksize)
        plt.rc('ytick', labelsize=self.defwinfmt.ticksize)
        return plotfigure

    def apply_trims(self, wcsc, *arrs):
        """Trim arrays as specofoed, adjusting wcs coords if needed"""

        self.trims.apply_wcs(wcsc)
        result = []
        for a in arrs:
            result.append(self.trims.apply_image(a))
        return tuple(result)


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
