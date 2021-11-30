"""outines for object info database"""

import xml.etree.ElementTree as ET
import datetime
import os.path
from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
import pymysql
import remdefaults
import xmlutil

DEFAULT_APSIZE = 6
Possible_filters = 'girzHJK'


class  ObjDataError(Exception):
    """Class to report errors concerning individual objects"""


def get_objname(dbcurs, alias, allobj=False):
    """Return unchanged name if if a main object name, otherwise find object name from alias ignoring suppressed objects unless allobj set"""
    dbcurs.execute("SELECT objname,suppress FROM objdata WHERE objname=%s", alias)
    f = dbcurs.fetchall()
    if len(f) > 0:
        name, supp = f[0]
        if supp and not allobj:
            raise ObjDataError("Known but suppressed", alias)
        return alias
    dbcurs.execute("SELECT objdata.objname,suppress FROM objalias INNER JOIN objdata WHERE objdata.objname=objalias.objname AND alias=%s", alias)
    f = dbcurs.fetchall()
    try:
        name, supp = f[0]
        if supp and not allobj:
            raise ObjDataError("Aliased to " + name + " but is suppressed", alias)
        return  name
    except IndexError:
        raise ObjDataError("Unknown object or alias name", alias)


def nameused(dbcurs, name):
    """Check if name is in use before manually adding it"""
    try:
        get_objname(dbcurs, name)
        return True
    except ObjDataError:
        return False


class ObjAlias:
    """Representation of the alias of an object"""

    def __init__(self, aliasname=None, objname=None, source=None, sbok=True):
        self.objname = objname
        self.aliasname = aliasname
        self.source = source
        self.sbok = sbok

    def get(self, dbcurs, aliasname=None):
        """Get alias from aliasname or already supplied one if not given"""

        if aliasname is None:
            aliasname = self.aliasname
        else:
            self.aliasname = aliasname

        if aliasname is None:
            raise ObjDataError("No alias name provided in ObjAlias object", "")

        dbcurs.execute("SELECT objname,source,sbok FROM objalias WHERE alias=%s", aliasname)
        f = dbcurs.fetchall()
        if len(f) == 0:
            raise ObjDataError("Alias not found", aliasname)
        self.objname, self.source, self.sbok = f[0]

    def put(self, dbcurs):
        """Write out alias to file"""

        if self.aliasname is None:
            raise ObjDataError("No alias name given", "")
        if self.objname is None:
            raise ObjDataError("No object name given for alias", self.aliasname)
        if self.source is None:
            raise ObjDataError("No source given for alias", self.aliasname)
        fieldnames = []
        fieldvalues = []
        conn = dbcurs.connection
        fieldnames.append("alias")
        fieldvalues.append(conn.escape(self.aliasname))
        fieldnames.append("objname")
        fieldvalues.append(conn.escape(self.objname))
        fieldnames.append("source")
        fieldvalues.append(conn.escape(self.source))
        fieldnames.append("sbok")
        if self.sbok:
            fieldvalues.append("1")
        else:
            fieldvalues.append("0")
        try:
            dbcurs.execute("INSERT INTO objalias (" + ",".join(fieldnames) + ") VALUES (" + ",".join(fieldvalues) + ")")
        except pymysql.MySQLError as e:
            if e.args[0] == 1062:
                raise ObjDataError("Duplicate alias " + self.aliasname + " object", self.objname)
            raise ObjDataError("Could not insert alias " + self.aliasname, e.args[1])

    def update(self, dbcurs):
        """Update object to database"""
        if self.aliasname is None:
            raise ObjDataError("No alias in ObjAlias", "")

        conn = dbcurs.connection
        fields = []
        if self.objname is not None:
            fields.append("objname=" + conn.escape(self.objname))
        if self.source is not None:
            fields.append("source=" + conn.escape(self.source))
        if self.sbok:
            fields.append("sbok=1")
        else:
            fields.append("sbok=0")

        try:
            dbcurs.execute("UPDATE objalias SET" + ",".join(fields) + " WHERE alias=" + conn.escape(self.aliasname))
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not update alias " + self.aliasname, e.args[1])

    def delete(self, dbcurs):
        """Delete alias"""
        if self.aliasname is None:
            raise ObjDataError("No alias in ObjAlias", "")
        n = 0
        try:
            n = dbcurs.execute("DELETE FROM objalias WHERE alias=%s", self.aliasname)
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not delete alias " + self.aliasname, e.args[1])
        if n == 0:
            raise ObjDataError("No alias to delete of name", self.aliasname)


class ObjData:
    """Decreipt an individaul object"""

    def __init__(self, objname=None, objtype=None, dispname=None):
        self.objname = self.dispname = objname
        self.objtype = objtype
        if dispname is not None:
            self.dispname = dispname
        self.vicinity = None
        self.dist = self.rv = self.ra = self.dec = self.rapm = self.decpm = None
        self.gmag = self.imag = self.rmag = self.zmag = self.Hmag = self.Jmag = self.Kmag = None
        self.apsize = DEFAULT_APSIZE
        self.invented = False
        self.usable = True
        self.suppress = False

    def get(self, dbcurs, name=None, allobj=False):
        """Get object by name"""

        if name is None:
            name = self.objname
            if name is None:
                raise ObjDataError("No name supplied for ObjData", "")
        if allobj:
            extra = ""
        else:
            extra = "suppress=0 AND "
        dbcurs.execute("SELECT objname,objtype,dispname,vicinity,dist,rv,radeg,decdeg,rapm,decpm,gmag,imag,rmag,zmag,Hmag,Jmag,Kmag,apsize,invented,usable,suppress FROM objdata WHERE " + extra + "objname=%s", get_objname(dbcurs, name, allobj=allobj))
        f = dbcurs.fetchall()
        if len(f) != 1:
            if len(f) == 0:
                raise ObjDataError("(warning) Object not found", name)
            raise ObjDataError("Internal problem too many objects with name", name)
        self.objname, self.objtype, self.dispname, self.vicinity, self.dist, self.rv, self.ra, self.dec, self.rapm, self.decpm, self.gmag, self.imag, self.rmag, self.zmag, self.Hmag, self.Jmag, self.Kmag, self.apsize, self.invented, self.usable, self.suppress = f[0]

    def is_target(self):
        """Report if it's the target by comparing with vicinity"""
        return  self.objname == self.vicinity

    def put(self, dbcurs):
        """Save object to database"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        if self.dispname is None:
            raise ObjDataError("No display name in ObjData for", self.objname)
        if self.vicinity is None:
            raise ObjDataError("No vicinity in ObjData for", self.objname)
        if self.ra is None or self.dec is None:
            raise ObjDataError("No coords in ObjData for", self.objname)
        conn = dbcurs.connection
        fieldnames = []
        fieldvalues = []

        fieldnames.append("objname")
        fieldvalues.append(conn.escape(self.objname))
        fieldnames.append("dispname")
        fieldvalues.append(conn.escape(self.dispname))
        fieldnames.append("vicinity")
        fieldvalues.append(conn.escape(self.vicinity))

        if self.objtype is not None:
            fieldnames.append("objtype")
            fieldvalues.append(conn.escape(self.objtype))

        if self.dist is not None:
            fieldnames.append("dist")
            fieldvalues.append("%.6g" % self.dist)

        if self.rv is not None:
            fieldnames.append("rv")
            fieldvalues.append("%.6g" % self.rv)

        fieldnames.append("radeg")
        fieldvalues.append("%.6g" % self.ra)
        fieldnames.append("decdeg")
        fieldvalues.append("%.6g" % self.dec)

        if self.rapm is not None:
            fieldnames.append("rapm")
            fieldvalues.append("%.6g" % self.rapm)
        if self.decpm is not None:
            fieldnames.append("decpm")
            fieldvalues.append("%.6g" % self.decpm)

        for f in Possible_filters:
            aname = f + "mag"
            val = getattr(self, aname, None)
            if val is not None:
                fieldnames.append(aname)
                fieldvalues.append("%.6g" % val)

        fieldnames.append("apsize")
        fieldvalues.append("%d" % self.apsize)
        fieldnames.append("invented")
        if self.invented:
            fieldvalues.append("1")
        else:
            fieldvalues.append("0")
        fieldnames.append("usable")
        if self.usable:
            fieldvalues.append("1")
        else:
            fieldvalues.append("0")

        try:
            dbcurs.execute("INSERT INTO objdata (" + ",".join(fieldnames) + ") VALUES (" + ",".join(fieldvalues) + ")")
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not insert object " + self.objname, e.args[1])

    def update(self, dbcurs):
        """Update object to database"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")

        conn = dbcurs.connection
        fields = []
        if self.dispname is not None:
            fields.append("dispname=" + conn.escape(self.dispname))
        if self.vicinity is not None:
            fields.append("vicinity=" + conn.escape(self.vicinity))
        if self.objtype is not None:
            fields.append("objtype=" + conn.escape(self.objtype))
        if self.dist is not None:
            fields.append("dist=%.6g" % self.dist)
        if self.rv is not None:
            fields.append("rv=%.6g" % self.rv)
        if self.ra is not None:
            fields.append("radeg=%.6g" % self.ra)
        if self.dec is not None:
            fields.append("decdeg=%.6g" % self.dec)
        if self.rapm is not None:
            fields.append("rapm=%.6g" % self.rapm)
        if self.decpm is not None:
            fields.append("decpm=%.6g" % self.decpm)
        for f in Possible_filters:
            aname = f + "mag"
            val = getattr(self, aname, None)
            if val is not None:
                fields.append("%s=%.6g" % (aname, val))
        fields.append("apsize=%d" % self.apsize)
        if self.invented:
            fields.append("invented=1")
        else:
            fields.append("invented=0")
        if self.usable:
            fields.append("usable=1")
        else:
            fields.append("usable=0")

        try:
            dbcurs.execute("UPDATE objdata SET " + ",".join(fields) + " WHERE objname=" + conn.escape(self.objname))
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not update object " + self.objname, e.args[1])

    def delete(self, dbcurs):
        """Delete data for object and also delete aliases for it"""

        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")

        n = 0
        try:
            dbcurs.execute("DELETE FROM objalias WHERE objname=%s", self.objname)
            n = dbcurs.execute("DELETE FROM objdata WHERE objname=%s", self.objname)
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not delete object " + self.objname, e.args[1])
        if n == 0:
            raise ObjDataError("No objects to delete of name", self.objname)

    def list_aliases(self, dbcurs, manonly=False):
        """Get a list of aliases for the object. If manonly is set just list manually entered ones"""

        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")

        dbcurs.execute("SELECT alias,source,sbok FROM objalias WHERE objname=%s", self.objname)
        f = dbcurs.fetchall()
        result = []
        for alias, source, sbok in f:
            if manonly and sbok:
                continue
            result.append(ObjAlias(aliasname=alias, objname=self.objname, source=source, sbok=sbok))
        return  result

    def list_allnames(self, dbcurs):
        """Get all the names and aliases of an object as a sorted list"""
        result = [a.aliasname for a in self.list_aliases(dbcurs)]
        result.append(self.objname)
        return sorted(result)

    def add_alias(self, dbcurs, aliasname, source, sbok=True):
        """Add an alias"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        ObjAlias(aliasname=aliasname, objname=self.objname, source=source, sbok=sbok).put(dbcurs)

    def delete_aliases(self, dbcurs):
        """Delete all aliases - do this when we recreate list"""
        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        dbcurs.execute("DELETE FROM objalias WHERE objname=%s", self.objname)

    def apply_motion(self, obstime):
        """Apply proper motion (mostly) to coordinates"""

        if self.objname is None:
            raise ObjDataError("No objname in ObjData", "")
        if self.ra is None or self.dec is None:
            raise ObjDataError("No coordinates found in objdata for", self.objname)
        if self.rapm is None or self.decpm is None:
            return
        if isinstance(obstime, datetime.date):
            obstime = datetime.datetime(obstime.year, obstime.month, obstime.day, 12, 0, 0)
        args = dict(ra=self.ra * u.deg, dec=self.dec * u.deg, obstime=Time('J2000'), pm_ra_cosdec=self.rapm * u.mas / u.yr, pm_dec=self.decpm * u.mas / u.yr)
        if self.dist is not None:
            args['distance'] = self.dist * u.lightyear
        if self.rv is not None:
            args['radial_velocity'] = self.rv * u.km / u.second
        spos = SkyCoord(**args).apply_space_motion(new_obstime=Time(obstime))
        self.ra = spos.ra.deg
        self.dec = spos.dec.deg
        if self.dist is not None:
            self.dist = spos.distance.lightyear


def get_objects(dbcurs, vicinity, obstime=None):
    """Get a list of objects in vicinity of named object
    Adjust for time if specified"""

    targname = get_objname(dbcurs, vicinity)  # Might give error if unknown
    dbcurs.execute("SELECT objname FROM objdata WHERE suppress=0 AND vicinity=%s", targname)
    onames = dbcurs.fetchall()

    results = []
    targobj = None

    for oname, in onames:
        obj = ObjData(oname)
        obj.get(dbcurs)
        if obj.is_target():
            targobj = obj
        else:
            results.append(obj)
    if targobj is None:
        raise ObjDataError("Could not find target objaect looking for", targname)
    results.insert(0, targobj)

    if obstime is not None:
        for r in results:
            r.apply_motion(obstime)
    return results


def prune_objects(objlist, ras, decs):
    """Prune list of objects to those within ranges of ras and decs given"""
    minra = min(ras)
    maxra = max(ras)
    mindec = min(decs)
    maxdec = max(decs)
    return [o for o in objlist if minra <= o.ra <= maxra and mindec <= o.dec <= maxdec]


Cached_fields = dict(objname=xmlutil.gettext, dispname=xmlutil.gettext, vicinity=xmlutil.gettext, objtype=xmlutil.gettext,
                     ra=xmlutil.getfloat, dec=xmlutil.getfloat, dist=xmlutil.getfloat,
                     origra=xmlutil.getfloat, origdec=xmlutil.getfloat, origdist=xmlutil.getfloat,
                     rv=xmlutil.getfloat, rapm=xmlutil.getfloat, decpm=xmlutil.getfloat, apsize=xmlutil.getint)
for possf in Possible_filters:
    Cached_fields[possf + 'mag'] = xmlutil.getfloat


class Cached_ObjData(ObjData):
    """Form of objdata for when we are caching to file"""

    def __init__(self, objname=None, objtype=None, dispname=None):

        super().__init__(objname, objtype, dispname)
        self.origra = None
        self.origdec = None
        self.origdist = None

    def get(self, dbcurs, name=None):
        """Revised get to remember initial ra and dec"""
        ObjData.get(self, dbcurs, name)
        self.origra = self.ra
        self.origdec = self.dec
        self.origdist = self.dist

    def apply_motion(self, obstime):
        """Apply motion reseting to orignial ra/dec first"""
        self.ra = self.origra
        self.dec = self.origdec
        self.dist = self.origdist
        ObjData.apply_motion(self, obstime)

    def in_region(self, minra, maxra, mindec, maxdec):
        """Check if object is in region"""
        return  minra <= self.ra <= maxra and mindec <= self.dec <= maxdec

    def load(self, node):
        """Load an object from XML file"""
        self.objname = self.dispname = self.vicinity = self.objtype = None
        self.dist = self.rv = self.ra = self.dec = self.dist = None
        self.origra = self.origdec = self.origdist = None
        self.rapm = self.decpm = None
        for f in Possible_filters:
            setattr(self, f + 'mag', None)
        self.apsize = DEFAULT_APSIZE
        self.invented = node.get("invented", 'n') == 'y'
        self.usable = node.get("unusable", 'n') != 'y'
        for child in node:
            try:
                setattr(self, child.tag, Cached_fields[child.tag](child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.invented:
            node.set("invented", 'y')
        if not self.usable:
            node.set("unusable", "y")
        for k in Cached_fields.keys():
            v = getattr(self, k, None)
            if v is not None:
                xmlutil.savedata(doc, node, k, v)


CACHEDOBJ_DOC_ROOT = "Cachedobj"


class Cached_Objlist:
    """Cached list of objects with tracking of dates"""

    def __init__(self, vicinity=None):
        self.fullcalc_date = None
        self.objlist = []
        self.vicinity = vicinity

    def numobjs(self):
        """Return number of objects"""
        return  len(self.objlist)

    def get_all(self, dbcurs, opdate, vicinity=None):
        """Get all objects from database to kick off with"""

        if vicinity is not None:
            self.vicinity = vicinity
        try:
            dbcurs.execute("SELECT objname FROM objdata WHERE suppress=0 AND vicinity=%s", get_objname(dbcurs, self.vicinity))
        except pymysql.MySQLError:
            raise ObjDataError("Invalid get all - is vicinity set right", "")
        self.objlist = []
        for obj, in dbcurs.fetchall():
            st = Cached_ObjData(obj)
            st.get(dbcurs)
            self.objlist.append(st)
        for obj in self.objlist:
            obj.apply_motion(opdate)
        self.fullcalc_date = opdate

    def prune_region(self, ras, decs):
        """Prune result to ones in region"""
        minra = min(ras)
        maxra = max(ras)
        mindec = min(decs)
        maxdec = max(decs)
        self.objlist = [o for o in self.objlist if o.in_region(minra, maxra, mindec, maxdec)]
        return self

    def adjust_proper_motions(self, newdate):
        """Adjust for proper motions"""
        difft = newdate - self.fullcalc_date.date()
        nyears = difft.days / 365.25
        newtime = newdate + difft
        for obj in self.objlist:
            if obj.rapm is None or obj.decpm is None:
                continue
            if abs(obj.rapm * nyears) >= 0.5 or abs(obj.decpm * nyears) >= 0.5:
                obj.apply_motion(newtime)

    def load(self, node):
        """Load from an XML DOM node"""
        self.fullcalc_date = None
        self.vicinity = None
        self.objlist = []
        for child in node:
            tagn = child.tag
            if tagn == "objs":
                for gc in child:
                    cobj = Cached_ObjData()
                    cobj.load(gc)
                    self.objlist.append(cobj)
            elif tagn == "calcdate":
                self.fullcalc_date = datetime.datetime.fromisoformat(xmlutil.gettext(child))
            elif tagn == "vicinity":
                self.vicinity = xmlutil.gettext(child)

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        if self.fullcalc_date is not None:
            xmlutil.savedata(doc, node, "calcdate", self.fullcalc_date.isoformat())
        if self.vicinity is not None:
            xmlutil.savedata(doc, node, "vicinity", self.vicinity)
        if len(self.objlist) != 0:
            gc = ET.SubElement(node, "objs")
            for obj in self.objlist:
                obj.save(doc, gc, "object")


def load_cached_objs_from_file(fname):
    """Load cached objs text file"""
    try:
        doc, root = xmlutil.load_file(fname, CACHEDOBJ_DOC_ROOT)
        cobj = Cached_Objlist()
        conode = root.find("OBJL")
        if conode is None:
            raise xmlutil.XMLError("No tree")
        cobj.load(conode)
    except xmlutil.XMLError as e:
        raise ObjDataError("Load of " + fname + " gave", e.args[0])
    return  cobj


def save_cached_objs_to_file(catchedobjs, filename):
    """Save results to results text file"""
    try:
        doc, root = xmlutil.init_save(CACHEDOBJ_DOC_ROOT, CACHEDOBJ_DOC_ROOT)
        catchedobjs.save(doc, root, "OBJL")
        xmlutil.complete_save(filename, doc)
    except xmlutil.XMLError as e:
        raise ObjDataError("Save of " + filename + " gave", e.args[0])


def get_sky_region(dbcurs, obj, datet, ras, decs):
    """Get region of sky using cache"""
    date = datet
    if isinstance(date, datetime.datetime):
        date = date.date()
    map_for_date = remdefaults.skymap_file(obj, date)
    if os.path.exists(map_for_date):
        result = load_cached_objs_from_file(map_for_date)
    else:
        nearest = remdefaults.nearest_skymap_file(obj, date)
        if nearest is None:
            result = Cached_Objlist(obj)
            result.get_all(dbcurs, date)
        else:
            nearest_file, nearest_date = nearest
            if abs((nearest_date - date).days) >= 365:
                result = Cached_Objlist(obj)
                result.get_all(dbcurs, date)
            else:
                result = load_cached_objs_from_file(nearest_file)
                result.adjust_proper_motions(nearest_date)

        save_cached_objs_to_file(result, map_for_date)

    return  result.prune_region(ras, decs)
