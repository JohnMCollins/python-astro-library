"""outines for object info database"""

import datetime
import pymysql
from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
import objident
import objposition
import objparam
import xmlutil
import remfits

# PM units

MAS_YR = u.mas / u.yr

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


def nameused(dbcurs, name, allobj=False):
    """Check if name is in use before manually adding it"""
    try:
        get_objname(dbcurs, name, allobj)
        return True
    except ObjDataError:
        return False


def nextname(dbcurs, prefix):
    """Get next name to invent with given prefix, appending -001 etc
    NB assuming exactly 3 digits"""
    dbcurs.execute("SELECT objname FROM objdata WHERE objname REGEXP %s ORDER BY objname DESC LIMIT 1", '^' + prefix + '(-\d\d\d)?$')
    exist = dbcurs.fetchall()
    if len(exist) == 0:
        if not nameused(dbcurs, prefix, True):
            return  prefix
        n = 0
    else:
        exist = exist[0][0]
        ebits = exist.split('-')
        lastc = ebits.pop()
        if '-'.join(ebits) == prefix:
            n = int(lastc)
        else:
            n = 0
    while 1:
        n += 1
        newname = "{:s}-{:03d}".format(prefix, n)
        if not nameused(dbcurs, newname, True):
            return newname


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


class ObjData(objparam.ObjParam):
    """Decreipt an individaul object"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.suppress = kwargs['suppress']
        except KeyError:
            self.suppress = False

    def get(self, dbcurs, name=None, ind=0):
        """Get object by name"""

        if ind != 0:
            selector = "ind={:d}".format(ind)
        elif name is not None:
            selector = "objname=" + dbcurs.connection.escape(get_objname(dbcurs, name, allobj=True))
        elif self.objind != 0:
            selector = "ind={:d}".format(self.objind)
        elif self.vicinity is not None and self.label is not None:
            selector = "vicinity=" + dbcurs.connection.escape(self.vicinity) + " and label=" + dbcurs.connection.escape(self.label)
        else:
            try:
                self.check_valid_id(check_vicinity=False)
            except objident.ObjIdentErr as e:
                raise ObjDataError(*e.args)
            selector = "objname=" + dbcurs.connection.escape(get_objname(dbcurs, self.objname, allobj=True))
            name = self.objname

        dbcurs.execute("SELECT ind,objname,objtype,dispname,latexname,vicinity,label," \
                       "dist,rv,radeg,decdeg,rapm,decpm," \
                       "apsize,irapsize,apstd,irapstd,basedon,irbasedon,variability,invented,usable," \
                       "suppress FROM objdata WHERE " + selector)
        f = dbcurs.fetchall()
        if len(f) != 1:
            if len(f) == 0:
                raise ObjDataError("(warning) Object not found", name)
            raise ObjDataError("Internal problem too many objects with name", name)
        self.objind, self.objname, self.objtype, self.dispname, self.latexname, self.vicinity, self.label, \
            self.dist, self.rv, self.ra, self.dec, self.rapm, self.decpm, \
            self.apsize, self.irapsize, self.apstd, self.irapstd, self.basedon, self.irbasedon, self.variability, \
            self.invented, self.usable, self.suppress = f[0]
        self.fix_dispname()
        self.get_mags(dbcurs, self.objind)

    def put(self, dbcurs):
        """Save object to database"""
        try:
            self.check_valid_id(check_vicinity=True)
            self.check_valid_posn()
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())
        except objposition.ObjPositionErr as e:
            raise ObjDataError(e.getmessage())

        fieldnames = []
        fieldvalues = []
        self.put_param(dbcurs, fieldnames, fieldvalues)

        try:
            dbcurs.execute("INSERT INTO objdata (" + ",".join(fieldnames) + ") VALUES (" + ",".join(fieldvalues) + ")")
            self.objind = dbcurs.lastrowid
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not insert object " + self.objname, e.args[1])

    def update(self, dbcurs):
        """Update object to database"""

        try:
            self.check_valid_id(check_dispname=True, check_vicinity=True, check_objind=True)
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())

        fields = []
        self.update_ident(dbcurs, fields)
        self.update_info(dbcurs, fields)
        self.update_position(fields)
        self.update_mags(fields)

        try:
            dbcurs.execute("UPDATE objdata SET " + ",".join(fields) + " WHERE objname=%s", self.objname)
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not update object " + self.objname, e.args[1])

    def delete(self, dbcurs):
        """Delete data for object and also delete aliases for it"""

        try:
            self.check_valid_id(check_dispname=False)
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())

        n = 0
        name = self.objname
        try:
            dbcurs.execute("DELETE FROM objalias WHERE objname=%s", name)
            n = dbcurs.execute("DELETE FROM objdata WHERE objname=%s", name)
        except pymysql.MySQLError as e:
            raise ObjDataError("Could not delete object " + name, e.args[1])
        if n == 0:
            raise ObjDataError("No objects to delete of name", name)

    def list_aliases(self, dbcurs, manonly=False):
        """Get a list of aliases for the object. If manonly is set just list manually entered ones"""

        try:
            self.check_valid_id(check_dispname=False)
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())

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
        try:
            self.check_valid_id(check_dispname=False)
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())
        ObjAlias(aliasname=aliasname, objname=self.objname, source=source, sbok=sbok).put(dbcurs)

    def delete_aliases(self, dbcurs):
        """Delete all aliases for an object"""
        try:
            self.check_valid_id(check_dispname=False)
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())
        dbcurs.execute("DELETE FROM objalias WHERE objname=%s", self.objname)

    def in_region_check(self, minra, maxra, mindec, maxdec):
        """Check if object is in region"""
        try:
            self.check_valid_posn()
        except objposition.ObjPositionErr as e:
            raise ObjDataError(e.getmessage())
        return  self.in_region(minra, maxra, mindec, maxdec)

    def apply_motion(self, dbcurs, obstime):
        """Apply proper motion to object for given obs time"""

        if self.rapm is None or self.decpm is None:
            return

        if isinstance(obstime, datetime.date):
            obstime_date = obstime
            obstime_datetime = datetime.datetime(obstime.year, obstime.month, obstime.day, 12, 0, 0)
        else:
            obstime_date = obstime.date()
            obstime_datetime = obstime

        if self.timebasedon == obstime_date:
            return

        dbcurs.execute("SELECT radeg,decdeg FROM objpm WHERE objind={:d} AND obsdate=%s".format(self.objind), "{:%Y-%m-%d}".format(obstime_date))
        radec = dbcurs.fetchone()
        if radec is not None:
            self.ra, self.dec = radec
            return

        args = dict(ra=self.ra * u.deg, dec=self.dec * u.deg, obstime=Time('J2000'), pm_ra_cosdec=self.rapm * MAS_YR, pm_dec=self.decpm * MAS_YR)

        if self.dist is not None:
            args['distance'] = self.dist * u.lightyear

        if self.rv is not None:
            args['radial_velocity'] = self.rv * u.km / u.second

        spos = SkyCoord(**args).apply_space_motion(new_obstime=Time(obstime_datetime))
        self.ra = spos.ra.deg
        self.dec = spos.dec.deg
        if self.dist is not None:
            self.dist = spos.distance.lightyear
        self.timebasedon = obstime_date
        dbcurs.execute("INSERT INTO objpm (objind,obsdate,radeg,decdeg) VALUES ({:d},%s,{:.9e},{:.9e})".format(self.objind, self.ra, self.dec), "{:%Y-%m-%d}".format(obstime_date))

    def apply_motion_check(self, dbcurs, obstime):
        """Apply proper motion (mostly) to coordinates"""

        try:
            self.check_valid_id(check_vicinity=True)
            self.check_valid_posn()
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())
        except objposition.ObjPositionErr as e:
            raise ObjDataError(e.getmessage())

        self.apply_motion(dbcurs, obstime)

    def load(self, node):
        """Load an object from XML file"""
        self.load_param(node)
        self.suppress = xmlutil.getboolattr(node, "suppress")

    def save(self, doc, pnode, name="object"):
        """Save to XML DOM node"""
        node = self.save_param(doc, pnode, name)
        xmlutil.setboolattr(node, "suppress", self.suppress)
        return  node

    def bri_sort(self, filt):
        """Sort key for object list"""
        v = getattr(self, filt + "bri", None)
        if v is not None:
            return  -v
        bris = []
        mags = []
        for f in 'griz':
            v = getattr(self, f+'bri', None)
            if v is not None:
                bris.append(v)
            v = getattr(self, f+'mag', None)
            if v is not None:
                mags.append(v)
        try:
            return -max(bris)
        except ValueError:
            pass
        try:
            return min(mags)
        except ValueError:
            return 1e6

def prune_objects(objlist, ras, decs):
    """Prune list of objects to those within ranges of ras and decs given"""
    minra = min(ras)
    maxra = max(ras)
    mindec = min(decs)
    maxdec = max(decs)
    return [o for o in objlist if o.in_region(minra, maxra, mindec, maxdec)]

def between_clause(colname, possibles):
    """Generate MySQL between clause for ra or dec"""
    return  "{:s} BETWEEN {:.9e} AND {:.9e}".format(colname, possibles.min(), possibles.max())

def get_sky_region(dbcurs, remfitsobj, maxvariability = 0.0, nosuppress = True, usableonly=True):
    """Get objects in region of sky for frame"""

    vicinity = get_objname(dbcurs, remfitsobj.target)
    fieldselections = ["vicinity=%s"]
    if nosuppress:
        fieldselections.append("suppress=0")
    if usableonly:
        fieldselections.append("usable!=0")
    fieldselections.append("variability<={:.6e}".format(maxvariability))
    pixrows, pixcols = remfitsobj.data.shape
    cornerpix = ((0, 0), (pixcols - 1, 0), (0, pixrows - 1), (pixcols - 1, pixrows - 1))
    cornerradec = remfitsobj.wcs.pix_to_coords(cornerpix)
    fieldselections.append(between_clause("radeg", cornerradec[:,0]))
    fieldselections.append(between_clause("decdeg", cornerradec[:,1]))

    dbcurs.execute("SELECT ind FROM objdata WHERE " + " AND ".join(fieldselections), vicinity)
    objrows = dbcurs.fetchall()

    objlist = []
    for objind, in objrows:
        obj = ObjData()
        obj.get(dbcurs, ind=objind)
        obj.apply_motion(dbcurs, remfitsobj.date)
        objlist.append(obj)

    # Sort into order of descending brightness
    return  sorted(objlist, key=lambda x: x.bri_sort(remfitsobj.filter))
