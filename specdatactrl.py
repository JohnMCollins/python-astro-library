# Spectral data control file

import numpy as np
import os.path
import glob
import string
import re

import xmlutil
import datarange

class SpecDataError(Exception):
    pass

class SpecDataArray(object):
    """This class holds a set of spectral data

       We use numpy arrays for both X and Y values after loading"""

    def __init__(self, filename, cols = ('xvalues', 'yvalues'), mjdate = 0.0, mbjdate = 0.0, hvc = 0.0):
        self.filename = filename
        self.cols = cols
        self.discount = None
        self.xvalues = None
        self.yvalues = None
        self.yerr = None
        self.ignored = None
        self.modjdate = mjdate
        self.modbjdate = mbjdate
        self.xoffset = None
        self.yoffset = None
        self.xscale = None
        self.yscale = None
        self.hvcorrect = hvc

    def loadfile(self, directory):
        """Load up spectral data from file

        Pass directory name and mod date"""
        
        if self.xvalues is not None: return
        fname = self.filename
        if not os.path.isabs(fname):
            fname = os.path.join(directory, fname)

        try:
            mat = np.loadtxt(fname)
        except IOError as e:
            raise SpecDataError(e.args[0])

        for cnum, field in enumerate(self.cols):
            try:
                setattr(self, field, mat[:,cnum])
            except IndexError:
                raise SpecDataError("No column " + str(cnum) + " (" + field + ") in data")
        self.ignored = None

    def skip(self, reason):
        """Set reason for skipping data"""
        self.discount = reason

    def is_skipped(self):
        """Return reason for skipping data if applicable otherwise false"""
        if self.discount is None: return False
        return self.discount
        
    def get_xvalues(self, inclall = True):
        """Get X values after applying offset and scaling"""

        if not inclall:
            sk = self.is_skipped()
            if sk:
                raise SpecDataError("Discounted data", self.filename, sk)

        res = self.xvalues
        if res is None:
            raise SpecDataError("Data for " + self.filename + " is not loaded")
        
        # Don't use += or -= or the whole array will be mangled

        if self.xscale is not None and self.xscale != 1.0:
            res = res * self.xscale
        if self.xoffset is not None and self.xoffset != 0.0:
            res = res + self.xoffset
        return res

    def get_yvalues(self, inclall = True):
        """Get Y values after applying offset and scaling"""

        if not inclall:
            sk = self.is_skipped()
            if sk:
                raise SpecDataError("Discounted data", self.filename, sk)
     
        res = self.yvalues
        if res is None:
            raise SpecDataError("Data for " + self.filename + " is not loaded")
        
        # Don't use += or -= or the whole array will be mangled

        if self.yscale is not None and self.yscale != 1.0:
            res = res * self.yscale
        if self.yoffset is not None self.yoffset != 0.0:
            res = res + self.yoffset
        return res

    def load(self, node):
        """Load from XML DOM node"""
        child = node.firstChild()
        self.filename = ""
        self.discount = None
        self.xvalues = None
        self.yvalues = None
        self.yerr = None
        self.ignored = None
        self.modjdate = 0.0
        self.modbjdate = 0.0
        self.xoffset = None
        self.yoffset = None
        self.xscale = None
        self.yscale = None
        self.hvcorrect = 0.0
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "filename":
                self.filename = xmlutil.gettext(child)
            elif tagn == "discount":
                self.discount = xmlutil.gettext(child)
            elif tagn == "modjdate":
                self.modjdate = xmlutil.getfloat(child)
            elif tagn == "modbjdate":
                self.modbjdate = xmlutil.getfloat(child)
            elif tagn == "xoffset":
                self.xoffset = xmlutil.getfloat(child)
            elif tagn == "xscale":
                self.xscale = xmlutil.getfloat(child)
            elif tagn == "yoffset":
                self.yoffset = xmlutil.getfloat(child)
            elif tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "hvcorrect":
                self.hvcorrect = xmlutil.getfloat(child)
            child = child.nextSibling()          

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = doc.createElement(name)
        xmlutil.savedata(doc, node, "filename", self.filename)
        if self.discount is not None:
            xmlutil.savedata(doc, node, "discount", self.discount)
        if self.modjdate != 0.0:
            xmlutil.savedata(doc, node, "modjdate", self.modjdate)
        if self.modbjdate != 0.0:
            xmlutil.savedata(doc, node, "modbjdate", self.modbjdate)
        if self.xoffset is not None:
            xmlutil.savedata(doc, node, "xoffset", self.xoffset)
        if self.xscale is not None:
            xmlutil.savedata(doc, node, "xscale", self.xscale)
        if self.yoffset is not None:
            xmlutil.savedata(doc, node, "yoffset", self.yoffset)
        if self.yscale is not None:
            xmlutil.savedata(doc, node, "yscale", self.yscale)
        if self.hvcorrect != 0.0:
            xmlutil.savedata(doc, node, "hvcorrect", self.hvcorrect)
        pnode.appendChild(node)

def parse_jd(field):
    """Parse Julian date, checking it looks right"""
    if field[0:2] != "24":
        raise SpecDataError("Do not believe " + field + " is Julian date")
    return  float(field[2:]) - 0.5

def parse_mjd(field):
    """Parse Modified Julian date, checking it looks right"""
    d = float(field)
    if d >= 2400000.0:
        raise SpecDataError("Do not believe " + field + " is Modified Julian date")
    return  d

class SpecDataList(object):
    """This class contains a list of spectral data"""

    def __init__(self, obsfname = "", cols = ('specfile', 'modjdate', 'modbjdate', 'hvcorrect'), spdcols = ('xvalues','yvalues')):
        
        if len(obsfname) != 0:
            if os.path.isabs(obsfname):
                self.dirname, self.obsfname = os.path.split(obsfname)
            else:
                cdir = os.getcwd()
                fname = os.path.join(cdir, obsfname)
                self.dirname, self.obsfname = os.path.split(fname)
        else:
            self.dirname = self.obsfname = ""
        self.cols = cols
        self.spdcols = spdcols
        self.xoffset = 0.0
        self.xscale = 1.0
        self.yoffset = 0.0
        self.yscale = 1.0
        self.datalist = []
        self.dirty = False

        # These are maximum and minimum X/Y values to save loading them each time

        self.maxminx = None
        self.maxminy = None

        # These are set up and used in the parsing routines
        self.currentfile = ""
        self.modjdate = 0.0
        self.modbjdate = 0.0
        self.hvcorrect = 0.0

    def parse_jdate(self, field):
        """Parse julian date"""
        self.modjdate = parse_jd(field)

    def parse_mjdate(self, field):
        """Parse modified julian date"""
        self.modjdate = parse_mjd(field)

    def parse_bjdate(self, field):
        """Parse barycentric date"""
        self.modbjdate = parse_jd(field)

    def parse_mbjdate(self, field):
        """Parse modified barycentric date"""
        self.modbjdate = parse_mjd(field)
   
    def parse_hvcorrect(self, field):
        """Parse heliocentric vel correction"""
        self.hvcorrect = float(field)

    def parse_filename(self, field):
        """If file name is given, check it's the one we were expecting"""
        if field != self.currentfile:
            raise SpecDataError("File name out of sync read " + field + " expecting " + self.currentfile)

    routs = dict(specfile = parse_filename, jdate = parse_jdate, modjdate = parse_mjdate, bjdate = parse_bjdate, modbjdate = parse_mbjdate, hvcorrect = parse_hvcorrect)
    
    def loadfile(self):
        """Load observation file and set up data list"""

        fname = os.path.join(self.dirname, self.obsfname)
        try:
            fin = open(fname)
        except IOError as e:
            raise SpecDataError("Cannot open obs time file - " + e.args[0])

        # Attempt to work out name of spectral data files assuming that the first 5 chars of the names is the same

        filelist = glob.glob(self.dirname + '/*')
        occs = dict()
        for f5 in [os.path.basename(ff)[0:5] for ff in filelist]:
            try:
                occs[f5] = occs[f5] + 1
            except KeyError:
                occs[f5] = 1
        revoccs = dict()
        for k,v in occs.items():
            revoccs[v] = k
        prefix = revoccs[max(occs.values())]
        filelist = glob.glob(self.dirname + '/' + prefix + '*')
        filelist = map(lambda x: os.path.basename(x), filelist)
        filelist.sort()

        # We now should have a sorted list of files in filelist
        
        self.datalist = []
        reparser = re.compile("\s+")
        for line in fin:
            line = string.strip(line)
            if len(line) == 0: continue
            data = reparser.split(line)
            self.currentfile = filelist.pop(0)
            self.modjdate = 0.0
            self.modbjdate = 0.0
            self.hvcorrect = 0.0
        
            for n, c in enumerate(self.cols):
                try:
                    parserout = SpecDataList.routs[c]
                    parserout(self, data[n])
                except KeyError:
                    raise SpecDataError("Unknown column name " + c + " in SpecDataList")
                except IndexError:
                    raise SpecDataError("Column number " + str(n) + " out of range in SpecDataList")
                
            newarray = SpecDataArray(self.currentfile, self.spdcols, self.modjdate, self.modbjdate, self.hvcorrect)
            if self.yscale != 1.0:
                newarray.yscale = self.yscale
            if self.yoffset != 0.0:
                newarray.yoffset = self.yoffset
            self.datalist.append(newarray)Beware!!!!
        fin.close()

    def loadfiles(self):
        """Load all the files"""
        for f in self.datalist:
            f.loadfile(self.dirname)

    def getmaxmin(self):
        """Return ((minx,maxx),(miny,maxy))"""

        if self.maxminx is None or self.maxminy is None:
            self.loadfiles()
            xvmins = []
            yvmins = []
            xvmaxes = []
            yvmaxes = []
            for f in self.datalist:
                try:
                    xv = f.get_xvalues(False)
                    yv = f.get_yvalues(False)
                    xvmins.append(xv.min())
                    xvmaxes.append(xv.max())
                    yvmins.append(yv.min())
                    yvmaxes.append(yv.max())
                except SpecDataError:
                    pass
            if len(xvmins) == 0:
                raise SpecDataError("Cannot find any X or Y values for max/min")
            self.maxminx = datarange.DataRange(min(xvmins),max(xvmaxes))
            self.maxminy = datarange.DataRange(min(yvmins),max(yvmaxes))
            self.dirty = True
        return (self.maxminx, self.maxminy)

    def reset_xscale(self):
        """Reset all the X scaling values"""
        self.xscale = 1.0
        self.xoffset = 0.0
        for d in self.datalist:
            d.xscale = None
            d.xoffset = None
        self.maxminx = None
        self.dirty = True

    def reset_yscale(self):
        """Reset all the Y scaling values"""
        self.yscale = 1.0
        self.yoffset = 0.0
        for d in self.datalist:
            d.yscale = None
            d.yoffset = None
        self.maxminy = None
        self.dirty = True

    def set_xscaleoffset(self, xs = 1.0, xo = 0.0, force = False):
        """Set the given X scale on the data, forcing every data item if required"""
        if force:
            for d in self.datalist:
                d.xscale = xs
                d.xoffset = xo
        else:
            if xs == self.xscale and xo == self.xoffset: return
            self.xscale = xs
            self.xoffset = xo
            for d in self.datalist:
                if d.xscale is None: d.xscale = xs
                if d.xoffset is None: d.xoffset = xo
        self.maxminx = None
        self.dirty = True
    
    def set_yscaleoffset(self, ys = 1.0, yo = 0.0):
        """Set the given Y scale on the data"""
        if ys == self.yscale and yo == self.yoffset: return
        self.yscale = ys
        self.yoffset = yo
        for d in self.datalist:
            d.yscale = ys
            d.yoffset = yo
        self.maxminy = None
        self.dirty = True

    def load(self, node):
        """Load control file from XML file"""
        child = node.firstChild()
        self.dirname = self.obsfname = ""
        self.cols = []
        self.spdcols = []
        self.xoffset = 0.0
        self.yoffset = 0.0
        self.xscale = 1.0
        self.yscale = 1.0
        self.datalist = []
        self.maxminx = None
        self.maxminy = None
        self.dirty = False
        while not child.isNull():
            tagn = child.toElement().tagName()
            if tagn == "dirname":
                self.dirname = xmlutil.gettext(child)
            elif tagn == "obsfname":
                self.obsfname = xmlutil.gettext(child)
            elif tagn == "obscols":
                ochild = child.firstChild()
                while not ochild.isNull():
                    self.cols.append(xmlutil.gettext(ochild))
                    ochild = ochild.nextSibling()
            elif tagn == "spcols":
                schild = child.firstChild()
                while not schild.isNull():
                    self.spdcols.append(xmlutil.gettext(schild))
                    schild = schild.nextSibling()
            elif tagn == "xoffset":
                self.yoffset = xmlutil.getfloat(child)
            elif tagn == "xscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "yoffset":
                self.yoffset = xmlutil.getfloat(child)
            elif tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "maxminx":
                self.maxminx = datarange.DataRange()
                self.maxminx.load(child)
            elif tagn == "maxminy":
                self.maxminy = datarange.DataRange()
                self.maxminy.load(child)
            elif tagn == "data":
                dnode = child.firstChild()
                while not dnode.isNull():
                    sa = SpecDataArray("")
                    sa.load(dnode)
                    self.datalist.append(sa)
                    dnode = dnode.nextSibling()                
            child = child.nextSibling()
        for d in self.datalist:
            d.cols = self.spdcols

    def save(self, doc, pnode, name):
        """Save to XML file"""
        node = doc.createElement(name)
        pnode.appendChild(node)
        if len(self.dirname) != 0:
            xmlutil.savedata(doc, node, "dirname", self.dirname)
        if len(self.obsfname) != 0:
            xmlutil.savedata(doc, node, "obsfname", self.obsfname)
        colsnode = doc.createElement("obscols")
        node.appendChild(colsnode)
        for c in self.cols: xmlutil.savedata(doc, colsnode, "oc", c)
        colsnode = doc.createElement("spcols")
        node.appendChild(colsnode)
        for c in self.spdcols: xmlutil.savedata(doc, colsnode, "sc", c)
        if self.yoffset != 0.0:
            xmlutil.savedata(doc, node, "yoffset", self.yoffset)
        if self.yscale != 1.0:
            xmlutil.savedata(doc, node, "yscale", self.yscale)
        if self.maxminx is not None:
            self.maxminx.save(doc, node, "maxminx")
        if self.maxminy is not None:
            self.maxminy.save(doc, node, "maxminy")
        dnode = doc.createElement("data")
        node.appendChild(dnode)
        for d in self.datalist:
            d.save(doc, dnode, "array")
        self.dirty = False

