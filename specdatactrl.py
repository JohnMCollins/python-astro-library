# Spectral data control file

import numpy as np
import os.path
import glob
import string
import re
import xml.etree.ElementTree as ET

import xmlutil
import datarange

class SpecDataError(Exception):
    pass

# This is the reference wavelength for working out the slope adjustment

Default_ref_wavelength = 6561.0

class SpecDataArray(object):
    """This class holds a set of spectral data

       We use numpy arrays for both X and Y values after loading"""

    def __init__(self, filename, cols = ('xvalues', 'yvalues'), mjdate = 0.0, mbjdate = 0.0, hvc = 0.0):
        self.filename = filename
        self.cols = cols
        self.discount = False
        self.remarks = None
        self.xvalues = None
        self.yvalues = None
        self.yerr = None
        self.ignored = None
        self.modjdate = mjdate
        self.modbjdate = mbjdate
        self.xoffset = None
        self.yoffset = None
        self.contslope = 0.0
        self.xscale = None
        self.yscale = None
        self.listlink = None
        self.hvcorrect = hvc

    def __hash__(self):
        return str.__hash__("%.6f" % self.modjdate)

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
        self.discount = True
        self.remarks = reason

    def is_skipped(self):
        """Return reason for skipping data if applicable otherwise false"""
        if not self.discount: return False
        return self.remarks
        
    def get_xvalues(self, inclall = True):
        """Get X values after applying offset and scaling"""

        if not inclall:
            sk = self.is_skipped()
            if sk:
                raise SpecDataError("Discounted data", self.filename, sk)

        res = self.xvalues
        if res is None:
            raise SpecDataError("Data for " + self.filename + " is not loaded")
        
        # Don't use += or -= below or the whole array will be mangled
        # Apply scaling and offsets.

        try:
            try: res = res * self.listlink.xscale
            except TypeError: pass
            try: res = res + self.listlink.xoffset
            except TypeError: pass
        except AttributeError:
            pass
        try: res = res * self.xscale
        except TypeError: pass
        try: res = res + self.xoffset
        except TypeError: pass 
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

        # Don't use += or -= below or the whole array will be mangled

        if self.listlink is not None:

            # First apply global ones

            try: res = res * self.listlink.yscale
            except TypeError: pass
            try: res = res + self.listlink.yoffset
            except TypeError: pass

            # We need xvalues if we have a slope on the continuum at all

            if self.listlink.contslope != 0.0 or self.contslope != 0.0:
                xvals = self.get_xvalues(True) - self.listlink.refwavelength
                res = res + xvals * self.listlink.contslope
            
            # Apply local ones

            try: res = res * self.yscale
            except TypeError: pass
            try: res = res + self.yoffset
            except TypeError: pass
            if self.contslope != 0.0:
                res = res + xvals * self.contslope
        else:
            try: res = res * self.yscale
            except TypeError: pass
            try: res = res + self.yoffset
            except TypeError: pass

        return res

    def load(self, node):
        """Load from XML DOM node"""
        self.filename = ""
        self.remarks = None
        self.discount = False
        self.xvalues = None
        self.yvalues = None
        self.yerr = None
        self.ignored = None
        self.modjdate = 0.0
        self.modbjdate = 0.0
        self.xoffset = None
        self.yoffset = None
        self.contslope = 0.0
        self.xscale = None
        self.yscale = None
        self.hvcorrect = 0.0
        for child in node:
            tagn = child.tag
            if tagn == "filename":
                self.filename = xmlutil.gettext(child)
            elif tagn == "discount":
                self.remarks = xmlutil.gettext(child)
                self.discount = not xmlutil.getboolattr(child, "nosupp")
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
            elif tagn == "contslope":
                self.contslope = xmlutil.getfloat(child)
            elif tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "hvcorrect":
                self.hvcorrect = xmlutil.getfloat(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        xmlutil.savedata(doc, node, "filename", self.filename)
        if self.remarks is not None:
            ch = xmlutil.savedata(doc, node, "discount", self.remarks)
            xmlutil.setboolattr(node, "nosupp", not self.discount)
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
        if self.contslope != 0.0:
            xmlutil.savedata(doc, node, "contslope", self.contslope)
        if self.hvcorrect != 0.0:
            xmlutil.savedata(doc, node, "hvcorrect", self.hvcorrect)

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
        self.refwavelength = Default_ref_wavelength
        self.cols = cols
        self.spdcols = spdcols
        self.xoffset = None
        self.xscale = None
        self.yoffset = None
        self.yscale = None
        self.contslope = 0.0
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
            newarray.listlink = self
            self.datalist.append(newarray)
        fin.close()

    def loadfiles(self, flist = None):
        """Load all the files"""
        if flist is None: flist = self.datalist
        for f in flist:
            f.loadfile(self.dirname)

    def loadmaxmin(self):
        """Load up maxes and mins for other routines"""
        if self.maxminx is not None and self.maxminy is not None: return
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

    def getmaxmin(self):
        """Return ((minx,maxx),(miny,maxy))"""
        self.loadmaxmin()
        return (self.maxminx, self.maxminy)

    def getmaxminx(self):
        """Get just max and min for x as tuple"""
        self.loadmaxmin()
        return (self.maxminx.lower, self.maxminx.upper)

    def getmaxminy(self):
        """Get just max and min for y as tuple"""
        self.loadmaxmin()
        return (self.maxminy.lower, self.maxminy.upper)
    
    def count_indiv_x(self):
        """Count number of individual scales or offsets in X values"""
        n = 0
        for d in self.datalist:
            if d.xscale is not None or d.xoffset is not None:
                n += 1
        return n

    def count_indiv_y(self):
        """Count number of individual scales or offsets in Y values"""
        n = 0
        for d in self.datalist:
            if d.yscale is not None or d.yoffset is not None:
                n += 1
        return n

    def reset_indiv_x(self):
        """Reset any individual scales and offsets"""
        for d in self.datalist:
            d.xscale = d.xoffset = None

    def reset_x(self):
        """Reset the X scale and offset"""
        xl = xu = 0.0
        if self.maxminx is not None:
            xl = self.maxminx.lower
            xu = self.maxminx.upper
        changes = False
        if self.xoffset is not None:
            xl -= self.xoffset
            xu -= self.xoffset
            self.xoffset = None
            changes = True
        if self.xscale is not None:
            xl /= self.xscale
            xu /= self.xscale
            self.xscale = None
            changes = True
        if changes:
            if self.maxminx is not None:
                self.maxminx = datarange.DataRange(xl, xu)
            self.dirty = True       

    def reset_indiv_y(self):
        """Reset any individual scales and offsets"""
        for d in self.datalist:
            d.yscale = d.yoffset = None
            d.contslope = 0.0

    def reset_y(self):
        """Reset the Y scale and offset"""
        yl = yu = 0.0
        if self.maxminy is not None:
            yl = self.maxminy.lower
            yu = self.maxminy.upper
        changes = False
        if self.yoffset is not None:
            yl -= self.yoffset
            yu -= self.yoffset
            self.yoffset = None
            changes = True
        if self.yscale is not None:
            yl /= self.yscale
            yu /= self.yscale
            self.yscale = None
            changes = True
        if self.contslope != 0.0:
            self.contslope = 0.0
            changes = True
        if changes:
            if self.maxminy is not None:
                self.maxminy = datarange.DataRange(yl, yu)
            self.dirty = True

    def set_xscale(self, newsc):
        """Set x scale and adjust min/max if needed"""
        change = newsc
        if self.xscale is not None:
            change /= self.xscale
        if change == 1.0: return
        if self.xoffset is not None:
            self.xoffset *= change
        if self.maxminx is not None:
            self.maxminx = datarange.DataRange(self.maxminx.lower * change, self.maxminx.upper * change)
        if newsc == 1.0:
            self.xscale = None
        else:
            self.xscale = newsc
        self.dirty = True

    def set_xoffset(self, newoff):
        """Set x offset and adjust min/max if needed"""
        change = newoff
        if self.xoffset is not None:
            change -= self.xoffset
        if change == 0.0: return
        if self.maxminx is not None:
            self.maxminx = datarange.DataRange(self.maxminx.lower + change, self.maxminx.upper + change)
        if newoff == 0.0:
            self.xoffset = None
        else:
            self.xoffset = newoff
        self.dirty = True

    def set_yscale(self, newsc):
        """Set y scale and adjust min/max if needed"""
        change = newsc
        if self.yscale is not None:
            change /= self.yscale
        if change == 1.0: return
        if self.maxminy is not None:
            self.maxminy = datarange.DataRange(self.maxminy.lower * change, self.maxminy.upper * change)
        if newsc == 1.0:
            self.yscale = None
        else:
            self.yscale = newsc
        self.dirty = True

    def adj_yscale(self, adj):
        """Adjust Y scale by dividing by given figure"""
        change = 1.0 / adj
        if self.yscale is not None:
            change *= self.yscale
        self.set_yscale(change)
        if self.yscale is None: return 1.0
        return self.yscale

    def set_yoffset(self, newoff):
        """Set y offset and adjust min/max if needed"""
        change = newoff
        if self.yoffset is not None:
            change -= self.yoffset
        if change == 0.0: return
        if self.yoffset is not None:
            self.yoffset *= change
        if self.maxminy is not None:
            self.maxminy = datarange.DataRange(self.maxminy.lower + change, self.maxminy.upper + change)
        if newoff == 0.0:
            self.yoffset = None
        else:
            self.yoffset = newoff
        self.dirty = True

    def set_contslope(self, conts):
        """Set continuum slope"""
        change = conts - self.contslope
        if change == 0.0: return
        self.maxminy = None
        self.contslope = conts
        self.dirty = True

    def adj_contslope(self, adj):
        """Adjust continuum slope"""
        if adj == 0.0: return
        self.contslope += adj
        self.dirty = True

    def set_refwavelength(self, val):
        """Adjust ref wavelength"""
        self.refwavelength = val
        self.dirty = True

    def load(self, node):
        """Load control file from XML file"""
        self.dirname = self.obsfname = ""
        self.cols = []
        self.spdcols = []
        self.xoffset = None
        self.yoffset = None
        self.xscale = None
        self.yscale = None
        self.contslope = 0.0
        self.refwavelength = Default_ref_wavelength
        self.datalist = []
        self.maxminx = None
        self.maxminy = None
        self.dirty = False
        for child in node:
            tagn = child.tag
            if tagn == "dirname":
                self.dirname = xmlutil.gettext(child)
            elif tagn == "obsfname":
                self.obsfname = xmlutil.gettext(child)
            elif tagn == "obscols":
                for ochild in child: self.cols.append(xmlutil.gettext(ochild))
            elif tagn == "spcols":
                for schild in child: self.spdcols.append(xmlutil.gettext(schild))
            elif tagn == "xoffset":
                self.yoffset = xmlutil.getfloat(child)
            elif tagn == "xscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "yoffset":
                self.yoffset = xmlutil.getfloat(child)
            elif tagn == "yscale":
                self.yscale = xmlutil.getfloat(child)
            elif tagn == "contslope":
                self.contslope = xmlutil.getfloat(child)
            elif tagn == "refwavel":
                self.refwavelength = xmlutil.getfloat(child)
            elif tagn == "maxminx":
                self.maxminx = datarange.DataRange()
                self.maxminx.load(child)
            elif tagn == "maxminy":
                self.maxminy = datarange.DataRange()
                self.maxminy.load(child)
            elif tagn == "data":
                for dnode in child:
                    sa = SpecDataArray("")
                    sa.load(dnode)
                    sa.listlink = self
                    self.datalist.append(sa)                
        for d in self.datalist:
            d.cols = self.spdcols

    def save(self, doc, pnode, name):
        """Save to XML file"""
        node = ET.SubElement(pnode, name)
        if len(self.dirname) != 0:
            xmlutil.savedata(doc, node, "dirname", self.dirname)
        if len(self.obsfname) != 0:
            xmlutil.savedata(doc, node, "obsfname", self.obsfname)
        colsnode = ET.SubElement(node, "obscols")
        for c in self.cols: xmlutil.savedata(doc, colsnode, "oc", c)
        colsnode = ET.SubElement(node, "spcols")
        for c in self.spdcols: xmlutil.savedata(doc, colsnode, "sc", c)
        if self.xoffset is not None and self.xoffset != 0.0:
            xmlutil.savedata(doc, node, "xoffset", self.xoffset)
        if self.xscale is not None and self.xscale != 1.0:
            xmlutil.savedata(doc, node, "xscale", self.xscale)
        if self.yoffset is not None and self.yoffset != 0.0:
            xmlutil.savedata(doc, node, "yoffset", self.yoffset)
        if self.yscale is not None and self.yscale != 1.0:
            xmlutil.savedata(doc, node, "yscale", self.yscale)
        if self.contslope != 0.0:
            xmlutil.savedata(doc, node, "contslope", self.contslope)
        xmlutil.savedata(doc, node, "refwavel", self.refwavelength)
        if self.maxminx is not None:
            self.maxminx.save(doc, node, "maxminx")
        if self.maxminy is not None:
            self.maxminy.save(doc, node, "maxminy")
        dnode = ET.SubElement(node, "data")
        for d in self.datalist:
            d.save(doc, dnode, "array")
        self.dirty = False

