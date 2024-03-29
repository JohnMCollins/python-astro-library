"""Save REM geom and display settings"""

import sys
import copy
import os
import xml.etree.ElementTree as ET
import xmlutil
import configfile
import matplotlib.pyplot as plt
import numpy as np
import miscutils


class RemGeomError(Exception):
    """Throw in case of errors"""


class Imlimits:
    """Remember maximum size we can use for each filter"""

    def __init__(self, filt=None, rows=1024, cols=1024):

        self.filter = filt
        self.rows = rows
        self.cols = cols

    def apply(self, imagearray):
        """Apply to image"""
        return imagearray[0:self.rows, 0:self.cols]

    def load(self, node):
        """Load from XML DOM"""

        self.filter = node.get("filter")
        for child in node:
            tagn = child.tag
            if tagn == "rows":
                self.rows = xmlutil.getint(child)
            elif tagn == "cols":
                self.cols = xmlutil.getint(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.filter:
            node.set("filter", self.filter)
        xmlutil.savedata(doc, node, "rows", self.rows)
        xmlutil.savedata(doc, node, "cols", self.cols)


class Trims:
    """Remember number of pixels to trim from each end of each frame"""

    def __init__(self):

        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0
        self.afterblank = False  # True means trim zeros or NaN first
        self.name = None

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
        self.afterblank = False
        self.name = node.get("name")

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
            elif tagn == "afterblank":
                self.afterblank = True

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.name:
            node.set("name", self.name)
        if self.left != 0:
            xmlutil.savedata(doc, node, "left", self.left)
        if self.right != 0:
            xmlutil.savedata(doc, node, "right", self.right)
        if self.top != 0:
            xmlutil.savedata(doc, node, "top", self.top)
        if self.bottom != 0:
            xmlutil.savedata(doc, node, "bottom", self.bottom)
        if self.afterblank:
            ET.SubElement(node, "afterblank")


class Divspec:
    """Preferences for division display"""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        """Initialise default values"""
        self.nocoords = False
        self.divisions = 8
        self.divprec = 3
        self.divthresh = 15
        self.racol = "#771111"
        self.deccol = "#771111"
        self.divalpha = 0.5

    def load(self, node):
        """Load parameters from XML file"""

        self.set_defaults()

        for child in node:
            tagn = child.tag
            if tagn == "nocoords":
                self.nocoords = True
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
        xmlutil.savedata(doc, node, "divisions", self.divisions)
        xmlutil.savedata(doc, node, "divprec", self.divprec)
        xmlutil.savedata(doc, node, "divthresh", self.divthresh)
        xmlutil.savedata(doc, node, "racol", self.racol)
        xmlutil.savedata(doc, node, "deccol", self.deccol)
        xmlutil.savedata(doc, node, "divalpha", self.divalpha)


class Objdisp:
    """Specify how objects are highlighted"""

    def __init__(self):
        self.set_defaults()

    def set_defaults(self):
        """Initialise to default values"""
        self.targcolour = "red"
        self.idcolour = "yellow"
        self.objcolour = "cyan"
        self.objalpha = 1.0
        self.objtextfs = 12
        self.objtextdisp = 30
        self.objfill = False

    def load(self, node):
        """Load from XML DOM tree"""
        self.set_defaults()
        for child in node:
            tagn = child.tag
            if tagn == "targcolour":
                self.targcolour = xmlutil.gettext(child)
            elif tagn == "idcolour":
                self.idcolour = xmlutil.gettext(child)
            elif tagn == "objcolour":
                self.objcolour = xmlutil.gettext(child)
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
        xmlutil.savedata(doc, node, "targcolour", self.targcolour)
        xmlutil.savedata(doc, node, "idcolour", self.idcolour)
        xmlutil.savedata(doc, node, "objcolour", self.objcolour)
        xmlutil.savedata(doc, node, "objalpha", self.objalpha)
        xmlutil.savedata(doc, node, "objtextfs", self.objtextfs)
        xmlutil.savedata(doc, node, "objtextdisp", self.objtextdisp)


class Winfmt:
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


def checkdups(lst, name):
    """Check for duplications in list"""
    if len(set(lst)) == len(lst):
        return
    dups = set([])
    for n in lst:
        if lst.count(n) > 1:
            dups.add(n)
    dl = [str(n) for n in sorted(list(dups))]
    raise RemGeomError(name + " has duplicate " + ' '.join(dl))


class greyscale:
    """This represents graycale parameters as either percentiles or standerd devs"""

    def __init__(self, n=""):
        self.name = n
        self.isperc = False
        self.isfixed = False
        self.inverse = False
        self.shades = []
        self.values = []

    def setname(self, name):
        """Set name careful not to use it after it's been hashed"""
        self.name = name

    def setscale(self, vals, colours, isinverse=False, isperc=False, isfixed=False):
        """Takes a list of values (percentiles or multiples of std dev (could be negative).
        isperc is True if percentiles - and 100 will be added.
        colours is list of colours 0 and 255 will be addedd.
        There should be 1 less colour than values"""

        if len(vals) != len(colours) + 1:
            raise RemGeomError("values length should be 1 more than colours")

        if min(colours) <= 0 or max(colours) >= 255:
            raise RemGeomError("Colours should be in range 1 to 254")

        if isperc and (min(vals) <= 0 or max(vals) >= 100):
            raise RemGeomError("Percentiles should be in range >0 and <100")

        checkdups(colours, "colours")
        if isperc:
            checkdups(vals, "percentiles")
        else:
            checkdups(vals, "values")

        self.isperc = isperc
        self.isfixed = isfixed
        self.inverse = isinverse
        self.values = vals
        self.shades = colours

    def disp_colours(self):
        """Get a list of colours suitable for print out"""
        return " ".join(["%d" % i for i in sorted(self.shades + [0, 255], reverse=self.inverse)])

    def disp_values(self):
        """Get a list of values suitable for print out"""
        return " ".join(["%.6g" % i for i in sorted(self.values)])

    def get_colours(self):
        """Get colours map ready for display"""

        if len(self.shades) == 0:
            raise RemGeomError("valujes and colours not set up yet")

        clist = sorted(self.shades + [0, 255], reverse=not self.inverse)
        return  ["#%.2x%.2x%.2x" % (i, i, i) for i in clist]

    def get_cmap(self, data):
        """Get divisions as requested from data"""

        if len(self.values) == 0:
            raise RemGeomError("valujes and colours not set up yet")

        if self.isfixed:
            return  sorted(self.values + [data.min(), data.max()])

        if self.isperc:
            return  np.percentile(data, sorted(self.values + [0.0, 100.0]))

        mv = data.mean()
        sv = data.std()
        vals = np.array(sorted(self.values)) * sv + mv

        # Limits might be inside range fudge if so

        if data.min() > vals[0]:
            vals = np.concatenate(((vals[0] * 2 - vals[1],), vals))
        else:
            vals = np.concatenate(((data.min(),), vals))
        if data.max() < vals[-1]:
            vals = np.concatenate((vals, (vals[-1] * 2 - vals[-2],)))
        else:
            vals = np.concatenate((vals, (data.max(),)))
        return vals

    def load(self, node):
        """Load from XML DOM tree"""
        self.name = ""
        self.isperc = False
        self.isfixed = False
        self.inverse = False
        self.shades = []
        self.values = []

        n = node.get("name")
        if n is not None:
            self.name = str(n)
        t = node.get("type", "s")
        if len(t) > 0:
            if t[0] == 'p':
                self.isperc = True
            elif t[0] == 'f':
                self.isfixed = True
        t = node.get("inverse", 'n')
        if len(t) > 0 and t[0] == 'y':
            self.inverse = True

        for child in node:
            tagn = child.tag
            if tagn == "shades":
                for gc in child:
                    self.shades.append(xmlutil.getint(gc))
            elif tagn == "values":
                for gc in child:
                    self.values.append(xmlutil.getfloat(gc))

    def save(self, doc, pnode, name):
        """Save to xml DOM node"""
        if len(self.name) == 0 or len(self.shades) < 2 or len(self.values) < 3:
            return
        node = ET.SubElement(pnode, name)
        node.set("name", self.name)
        if self.isfixed:
            node.set("type", "fixed")
        elif self.isperc:
            node.set("type", "percent")
        if self.inverse:
            node.set("inverse", "y")
        cnode = ET.SubElement(node, "shades")
        for s in self.shades:
            xmlutil.savedata(doc, cnode, "s", s)
        cnode = ET.SubElement(node, "values")
        for v in self.values:
            xmlutil.savedata(doc, cnode, "v", v)


class RemGeom:
    """Represent common parameters for Rem programs"""

    def __init__(self):
        self.imlims = dict()
        self.curtrims = self.deftrims = Trims()
        self.ftrims = dict()
        self.divspec = Divspec()
        self.objdisp = Objdisp()
        self.defwinfmt = Winfmt()
        self.altfmts = dict()
        self.shades = dict()
        self.greyscales = dict()
        self.defgreyscale = None
        plt.rcParams['savefig.directory'] = os.getcwd()

    def list_altfmts(self):
        """Get a list of alternative formats"""
        return sorted(self.altfmts.keys())

    def load(self, node):
        """Load parameters from XML file"""

        self.imlims = dict()
        self.curtrims = self.deftrims = Trims()
        self.ftrims = dict()
        self.divspec = Divspec()
        self.defwinfmt = Winfmt()
        self.altfmts = dict()
        self.greyscales = dict()
        self.defgreyscale = None

        for child in node:
            tagn = child.tag
            if tagn == "imlims":
                for gc in child:
                    il = Imlimits()
                    il.load(gc)
                    if il.filter is not None:
                        self.imlims[il.filter] = il
            elif tagn == "trims":
                self.deftrims.load(child)
            elif tagn == "ftrim":
                for gc in child:
                    ft = Trims()
                    ft.load(gc)
                    if ft.name:
                        self.ftrims[ft.name] = ft
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
            elif tagn == "greyscales":
                for gc in child:
                    gs = greyscale()
                    gs.load(gc)
                    self.greyscales[gs.name] = gs
            elif tagn == "defgreyscale":
                self.defgreyscale = xmlutil.gettext(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if len(self.imlims) != 0:
            cnode = ET.SubElement(node, "imlims")
            for il in self.imlims.values():
                il.save(doc, cnode, "imlim")
        self.deftrims.save(doc, node, "trims")
        if len(self.ftrims) != 0:
            cnode = ET.SubElement(node, "ftrim")
            for ft in self.ftrims.values():
                ft.save(doc, cnode, "trim")
        self.divspec.save(doc, node, "divspec")
        self.objdisp.save(doc, node, "objdisp")
        self.defwinfmt.save(doc, node, "defwinfmt")
        if len(self.altfmts) != 0:
            afn = ET.SubElement(node, "altfmts")
            for k, v in self.altfmts.items():
                v.save(doc, afn, k)
        if len(self.greyscales) != 0:
            gss = ET.SubElement(node, "greyscales")
            for gs in self.greyscales.values():
                gs.save(doc, gss, "greyscale")
        if self.defgreyscale is not None:
            xmlutil.savedata(doc, node, "defgreyscale", self.defgreyscale)

    def disp_argparse(self, argp, fmt=None):
        """Initialise arg parser with display options"""
        if fmt is None:
            try:
                fmt = os.environ['REMGEOMFMT']
            except KeyError:
                pass
        which = self.defwinfmt
        if fmt in self.altfmts:     # Covers None case
            which = self.altfmts[fmt]
        argp.add_argument('--width', type=float, default=which.width, help="Width of figure")
        argp.add_argument('--height', type=float, default=which.height, help="Height of figure")
        argp.add_argument('--labsize', type=int, default=which.labsize, help='Label and title font size')
        argp.add_argument('--ticksize', type=int, default=which.ticksize, help='Tick font size')
        argp.add_argument('--objtextfs', type=int, default=self.objdisp.objtextfs, help='Object label text font size')
        argp.add_argument('--objtextdisp', type=int, default=self.objdisp.objtextdisp, help='Object label text displacement')
        argp.add_argument('--outfig', type=str, help='Output figure prefix if required')

#     def trim_argparse(self, argp):
#         """Initialise arg parser with trim options"""
#         argp.add_argument('--trimbottom', type=int, default=self.trims.bottom, help='Pixels to trim off bottom of picture')
#         argp.add_argument('--trimleft', type=int, default=self.trims.left, help='Pixels to trim off left of picture')
#         argp.add_argument('--trimright', type=int, default=self.trims.right, help='Pixels to trim off right of picture')
#         argp.add_argument('--trimtop', type=int, default=self.trims.top, help='Pixels to trim off top of picture')

    def disp_getargs(self, resargs):
        """Get arguments and reset parameters

        BN overwirtes defaults"""

        try:
            self.defwinfmt.width = resargs['width']
            self.defwinfmt.height = resargs['height']
            self.defwinfmt.labsize = resargs['labsize']
            self.defwinfmt.ticksize = resargs['ticksize']
            self.objdisp.objtextfs = resargs['objtextfs']
            self.objdisp.objtextdisp = resargs['objtextdisp']
            outfig = resargs['outfig']
        except KeyError as e:
            print("Error in parsed arguments", e.args[0], "is missing", file=sys.stderr)
            sys.exit(200)

        return outfig

#     def trim_getargs(self, resargs):
#         """Get argi,emts fpr tro,s"""
#         try:
#             self.trims.left = resargs['trimleft']
#             self.trims.right = resargs['trimright']
#             self.trims.top = resargs['trimtop']
#             self.trims.bottom = resargs['trimbottom']
#         except KeyError as e:
#             print("Error in parsed arguments", e.args[0], "is missing", file=sys.stderr)
#             sys.exit(200)

    def plt_figure(self):
        """Create plot figure and return it. Initialise tick size"""
        plotfigure = plt.figure(figsize=(self.defwinfmt.width, self.defwinfmt.height))
        plt.rc("font", size=self.defwinfmt.labsize)
        # plt.rc('fontsize', fontsize=self.defwinfmt.labsize)
        plt.rc('xtick', labelsize=self.defwinfmt.ticksize)
        plt.rc('ytick', labelsize=self.defwinfmt.ticksize)
        return plotfigure

    def select_trim(self, filt=None, create=False):
        """Select the appropriate trim for the filter and return whether we trim Nan/Zero first"""
        self.curtrims = self.deftrims
        if filt is not None:
            try:
                self.curtrims = self.ftrims[filt]
            except KeyError:
                if create:
                    self.curtrims = self.ftrims[filt] = copy.copy(self.deftrims)
                    self.curtrims.name = filt
        return self.curtrims.afterblank

    def apply_trims(self, wcsc, *arrs):
        """Trim arrays as specofoed, adjusting wcs coords if needed"""

        self.curtrims.apply_wcs(wcsc)
        result = []
        for a in arrs:
            result.append(self.curtrims.apply_image(a))
        return tuple(result)

    def get_imlim(self, filt):
        """Get image limits for filter"""
        try:
            return self.imlims[filt]
        except KeyError:
            return Imlimits(filt=filt)

    def set_imlim(self, il):
        """Set image limits for filter"""
        if il.filter is not None:
            self.imlims[il.filter] = il

    def list_greyscales(self):
        """Get a sorted list of gray scales"""
        return sorted([i.name for i in self.greyscales.values()])

    def get_greyscale(self, name):
        """Get corresponding gray sacle"""
        try:
            return self.greyscales[name]
        except KeyError:
            return None

    def del_greyscale(self, name):
        """Delete gray scale"""
        try:
            del self.greyscales[name]
            if self.defgreyscale == name:
                self.defgreyscale = None
        except KeyError:
            pass

    def set_greyscale(self, gs):
        """Set up greyscale"""
        if len(gs.name) == 0:
            raise RemGeomError("No name in gray scale")
        if len(gs.shades) < 1 or len(gs.values) < 2:
            raise RemGeomError("gray scale not set up in full " + str(len(gs.shades)) + " shades " + str(len(gs.values)) + " values")
        self.greyscales[gs.name] = gs

    def set_defgreyscale(self, name):
        """Set default greyscale"""
        if name not in self.greyscales:
            raise RemGeomError("Unknown grey scale " + name)
        self.defgreyscale = name

    def radecgridplt(self, w, dat):

        """Plot RA/DEC grid on image.

            w is a "scscoord" structure
            dat is the immage"""

        if self.divspec.nocoords:
            return

        # Get coords of edges of picture

        pixrows, pixcols = dat.shape
        cornerpix = ((0, 0), (pixcols - 1, 0), (9, pixrows - 1), (pixcols - 1, pixrows - 1))
        cornerradec = w.pix_to_coords(cornerpix)
        isrotated = abs(cornerradec[0, 0] - cornerradec[1, 0]) < abs(cornerradec[0, 0] - cornerradec[2, 0])

        # Get matrix of ra/dec each pixel

        pixarray = np.array([[(x, y) for x in range(0, pixcols)] for y in range(0, pixrows)])
        pixcoords = w.pix_to_coords(pixarray.reshape(pixrows * pixcols, 2)).reshape(pixrows, pixcols, 2)
        ratable = pixcoords[:, :, 0]
        dectable = pixcoords[:, :, 1]
        ramax, decmax = cornerradec.max(axis=0)
        ramin, decmin = cornerradec.min(axis=0)

        radivs = np.linspace(ramin, ramax, self.divspec.divisions).round(self.divspec.divprec)
        decdivs = np.linspace(decmin, decmax, self.divspec.divisions).round(self.divspec.divprec)

        ra_x4miny = []
        ra_y4minx = []
        ra_xvals = []
        ra_yvals = []
        dec_x4miny = []
        dec_y4minx = []
        dec_xvals = []
        dec_yvals = []

        for r in radivs:
            ra_y = np.arange(0, pixrows)
            diffs = np.abs(ratable - r)
            ra_x = diffs.argmin(axis=1)
            sel = (ra_x > 0) & (ra_x < pixcols - 1)
            ra_x = ra_x[sel]
            ra_y = ra_y[sel]
            if len(ra_x) == 0:
                continue
            if ra_y[0] < self.divspec.divthresh:
                ra_x4miny.append(ra_x[0])
                ra_xvals.append(r)
            if ra_x.min() < self.divspec.divthresh:
                ra_y4minx.append(ra_y[ra_x.argmin()])
                ra_yvals.append(r)
            plt.plot(ra_x, ra_y, color=self.divspec.racol, alpha=self.divspec.divalpha)

        for d in decdivs:
            dec_x = np.arange(0, pixcols)
            diffs = np.abs(dectable - d)
            dec_y = diffs.argmin(axis=0)
            sel = (dec_y > 0) & (dec_y < pixrows - 1)
            dec_x = dec_x[sel]
            dec_y = dec_y[sel]
            if len(dec_x) == 0:
                continue
            if dec_x[0] < self.divspec.divthresh:
                dec_y4minx.append(dec_y[0])
                dec_yvals.append(d)
            if dec_y.min() < self.divspec.divthresh:
                dec_x4miny.append(dec_x[dec_y.argmin()])
                dec_xvals.append(d)
            plt.plot(dec_x, dec_y, color=self.divspec.deccol, alpha=self.divspec.divalpha)

        fmt = '%.' + str(self.divspec.divprec) + 'f'

        if isrotated:
            rafmt = [fmt % r for r in ra_yvals]
            decfmt = [fmt % d for d in dec_xvals]
            plt.yticks(ra_y4minx, rafmt)
            plt.xticks(dec_x4miny, decfmt)
            plt.ylabel('RA (deg)')
            plt.xlabel('Dec (deg)')
        else:
            rafmt = [fmt % r for r in ra_xvals]
            decfmt = [fmt % d for d in dec_yvals]
            plt.xticks(ra_x4miny, rafmt)
            plt.yticks(dec_y4minx, decfmt)
            plt.xlabel('RA (deg)')
            plt.ylabel('Dec (deg)')


def load(fname=None, mustexist=False):
    """Load config geom from file"""
    if fname is None:
        fname = "remgeom"
    ret = RemGeom()
    try:
        dr = configfile.load(fname, "REMGEOM")
    except configfile.ConfigError as e:
        raise RemGeomError(e.args[0])
    if dr is None:
        if mustexist:
            raise RemGeomError("Cannot open " + fname)
        return ret
    (doc, root) = dr
    for child in root:
        if child.tag == "remg":
            ret.load(child)
    return ret


def save(rg, fname=None):
    """Save config to file"""
    if fname is None:
        fname = "remgeom"
    (doc, root) = configfile.init_save("REMGEOM")
    rg.save(doc, root, "remg")
    try:
        configfile.complete_save(doc, fname)
    except configfile.ConfigError as e:
        raise RemGeomError(e.args[0])

def end_figure(fig, filename, filenum=1, multi=False):
    """End a single figure, save to file if savng files.
    If multi is True, put _nnn filename after name and before .png"""
    if filename is None:
        return
    if multi:
        filename = miscutils.removesuffix(filename) + "_{:03d}.png".format(filenum)
    else:
        filename = miscutils.replacesuffix(filename, "png")
    fig.savefig(filename)
    plt.close(fig)

def end_plot(filename):
    """End whole plot, protect against interrupts"""
    if filename is None:
        try:
            plt.show()
        except KeyboardInterrupt:
            pass
