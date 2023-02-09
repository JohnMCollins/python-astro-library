"""Store interactive information about adjustments to objects"""

import re
import os.path
import remdefaults
import objdata

nmatch = re.compile("(.+)-(\d\d\d)+")


class ObjEditErr(Exception):
    """Raise if error found"""

class ObjEdit:
    """Edit item for an object"""

    Field_attrs = dict(op='s', objname='s', dispname='s', latexname='s', obsfile='s',
                       ind='d', objind='d',
                       apsize='f', nrow='f', ncol='f', radeg='f', decdeg='f',
                       done='b')
    Init_types = dict(s=None, d=0, f=0.0, b=False)
    Conv_code = dict(s="{:s}", d="{:d}", f="{:.9e}", b="{:d}")

    def __init__(self, **kwargs):
        self.done = False
        self.obj = None
        self.ind = 0
        for col, typ in ObjEdit.Field_attrs.items():
            setattr(self, col, ObjEdit.Init_types[typ])
        for arg, val in kwargs.items():
            if arg in ObjEdit.Field_attrs:
                setattr(self, arg, val)

    def loaddb(self, dbcurs, ind):
        """Load from database known ind"""
        dbcurs.execute("SELECT " + ",".join(ObjEdit.Field_attrs) + " FROM objedit WHERE ind={:d}".format(ind))
        r = dbcurs.fetchone()
        if r is None:
            raise ObjEditErr("Cannot get ObjEdit for {:s}".format(ind))
        for n, f in enumerate(ObjEdit.Field_attrs):
            setattr(self, f, r[n])
        if self.objind is not None:
            self.obj = objdata.ObjData()
            self.obj.get(dbcurs, ind = self.objind)

    def savedb(self, dbcurs):
        """Save new item to database"""
        fields = []
        values = []
        for col, typ in ObjEdit.Field_attrs.items():
            defv = ObjEdit.Init_types[typ]
            val = getattr(self, col, defv)
            if val != defv and col != "ind":
                fields.append(col)
                if typ == 's':
                    values.append(dbcurs.connection.escape(val))
                else:
                    values.append(ObjEdit.Conv_code[typ].format(val))
        if len(fields) == 0:
            raise ObjEditErr("No values given for ObjEdit")
        n = dbcurs.execute("INSERT INTO objedit (" + ",".join(fields) + ") VALUES (" + ",".join(values) + ")")
        if n == 0:
            raise ObjEditErr("Insert failed into objedit")
        self.ind = dbcurs.lastrowid

    def updatedb(self, dbcurs):
        """Update an item on datebase"""
        fields = []
        for col, typ in ObjEdit.Field_attrs.items():
            if col == "ind":
                continue
            defv = ObjEdit.Init_types[typ]
            val = getattr(self, col, defv)
            if typ == 's':
                if val is None:
                    val = "NULL"
                else:
                    val = dbcurs.connection.escape(val)
            else:
                val = ObjEdit.Conv_code[typ].format(val)
            fields.append("{:s}={:s}".format(col, val))
        dbcurs.execute("UPDATE objedit SET " + ",".join(fields) + "WHERE ind={:d}".format(self.ind))

    def setdone(self, dbcurs, done = True):
        """Specifically set done or unset it"""
        if self.done == done:
            return
        dbcurs.execute("UPDATE objedit SET done={:d} WHERE ind={:d}".format(done, self.ind))
        self.done = done

class ObjEdit_List:
    """Class for editing list of object edits"""

    def __init__(self):
        self.editlist = []
        self.namelist = set()

    def get_next(self):
        """Iterator for edits"""
        for fr in self.editlist:
            yield  fr

    def num_edits(self):
        """Return number of edits loaded"""
        return  len(self.editlist)

    def load_findres(self, fr):
        """Load names from find_results"""
        for res in fr.results():
            if res.obj is not None:
                self.namelist.add(res.obj.objname)

    def add_edit(self, edit):
        """Add edit to list"""
        self.editlist.append(edit)

    def nameok(self, dbase, name):
        """Check if name is OK and doesn't clash with anything"""
        return  not (objdata.nameused(dbase, name, True) or name in self.namelist)

    def getname(self, dbase, startname):
        """Get next name possibility"""
        if objdata.nameused(dbase, startname, True):
            startname = objdata.nextname(dbase, startname)
        if startname not in self.namelist:
            self.namelist.add(startname)
            return startname
        n = 0
        mtchs = nmatch.match(startname)
        if mtchs:
            startname, n = mtchs.groups()
            n = int(n)
        while 1:
            n += 1
            newname = "{:s}-{:03d}".format(startname, n)
            if self.nameok(dbase, newname):
                self.namelist.add(newname)
                return  newname

    def loaddb(self, dbcurs, notdone = True):
        """Load up list of edits from DB"""
        self.editlist = []
        wh = ""
        if notdone:
            wh = " WHERE done=0"
        dbcurs.execute("SELECT ind FROM objedit" + wh)
        for oer, in dbcurs.fetchall():
            oe = ObjEdit()
            oe.loaddb(dbcurs, oer)
            self.editlist.append(oe)
            if oe.obj is not None and oe.obj.objname is not None:
                self.namelist.add(oe.obj.objname)

    def savedb(self, dbcurs):
        """Save list of edits to database"""
        donesave = 0
        for oe in self.editlist:
            oe.savedb(dbcurs)
            donesave += 1
        if donesave != 0:
            dbcurs.connection.commit()

    def deldb(self, dbcurs, doneonly=True):
        """Delete from DB"""
        wh = ""
        if doneonly:
            wh = " WHERE done!=0"
        if  dbcurs.execute("DELETE FROM objedit" + wh) != 0:
            dbcurs.connection.commit()
