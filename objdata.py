"""outines for object info database"""

import datetime
import pymysql
import objident
import objposition
import objparam
import xmlutil


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
        else:
            try:
                self.check_valid_id(check_vicinity=False)
            except objident.ObjIdentErr as e:
                raise ObjDataError(e.getmessage())
            selector = "objname=" + dbcurs.connection.escape(get_objname(dbcurs, self.objname, allobj=True))
            name = self.objname

        dbcurs.execute("SELECT ind,objname,objtype,dispname,vicinity," \
                       "dist,rv,radeg,decdeg,rapm,decpm," \
                       "apsize,irapsize,apstd,irapstd,basedon,irbasedon,invented,usable," \
                       "suppress FROM objdata WHERE " + selector)
        f = dbcurs.fetchall()
        if len(f) != 1:
            if len(f) == 0:
                raise ObjDataError("(warning) Object not found", name)
            raise ObjDataError("Internal problem too many objects with name", name)
        self.objind, self.objname, self.objtype, self.dispname, self.vicinity, \
            self.dist, self.rv, self.ra, self.dec, self.rapm, self.decpm, \
            self.apsize, self.irapsize, self.apstd, self.irapstd, self.basedon, self.irbasedon, self.invented, self.usable, self.suppress = f[0]
        self.save_pos()
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

    def apply_motion_check(self, obstime):
        """Apply proper motion (mostly) to coordinates"""

        try:
            self.check_valid_id(check_vicinity=True)
            self.check_valid_posn()
        except objident.ObjIdentErr as e:
            raise ObjDataError(e.getmessage())
        except objposition.ObjPositionErr as e:
            raise ObjDataError(e.getmessage())

        self.apply_motion(obstime)

    def load(self, node):
        """Load an object from XML file"""
        self.load_param(node)
        self.suppress = xmlutil.getboolattr(node, "suppress")

    def save(self, doc, pnode, name="object"):
        """Save to XML DOM node"""
        node = self.save_param(doc, pnode, name)
        xmlutil.setboolattr(node, "suppress", self.suppress)
        return  node


def prune_objects(objlist, ras, decs):
    """Prune list of objects to those within ranges of ras and decs given"""
    minra = min(ras)
    maxra = max(ras)
    mindec = min(decs)
    maxdec = max(decs)
    return [o for o in objlist if o.in_region(minra, maxra, mindec, maxdec)]


def get_sky_region(dbcurs, vicinity, datet, ras, decs):
    """Get objects in region of sky and djust proper motions"""

    # Normalise date

    date = datet
    if isinstance(date, datetime.datetime):
        date = date.date()

    # First get ourselves a list of objects

    vicinity = get_objname(dbcurs, vicinity)
    dbcurs.execute("SELECT ind FROM objdata WHERE suppress=0 AND vicinity=%s", vicinity)
    objlist = []
    for ind, in dbcurs.fetchall():
        st = ObjData(ind=ind)
        st.get(dbcurs)
        objlist.append(st)

    # Adjust coords for things with proper mtions
    # First get any we've cached

    cached_by_id = dict()
    fmtdate = date.strftime("%Y-%m-%d")
    dbcurs.execute("SELECT objpm.objind,objpm.radeg,objpm.decdeg,objpm.dist " \
                   "FROM objpm INNER JOIN objdata " \
                   "WHERE objpm.objind=objdata.ind " \
                   "AND objpm.obsdate=%s " \
                   "AND objdata.vicinity=%s", (fmtdate, vicinity))
    for ind, radeg, decdeg, dist in dbcurs.fetchall():
        cached_by_id[ind] = (radeg, decdeg, dist)

    # Count ones we've added to cache

    added = 0

    for obj in objlist:
        ind = obj.objind
        try:
            radeg, decdeg, dist = cached_by_id[ind]
            obj.save_pos()
            obj.ra = radeg
            obj.dec = decdeg
            obj.dist = dist
            continue
        except KeyError:
            pass

        # Not cached in DB, work it out and add to DB

        obj.apply_motion(date)
        fields = ["objind", "obsdate", "radeg", "decdeg" ]
        values = [str(ind), dbcurs.connection.escape(fmtdate), str(obj.ra), str(obj.dec)]
        if obj.dist is not None:
            fields.append("dist")
            values.append(str(dist))
        dbcurs.execute("INSERT INTO objpm (" + ",".join(fields) + ") VALUES (" + ",".join(values) + ")")
        cached_by_id[ind] = (obj.ra, obj.dec, obj.dist)
        added += 1

    return prune_objects(objlist, ras, decs)
