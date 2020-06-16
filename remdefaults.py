# Save options in home control file for later recovery

import os
import os.path
import sys
import dbops

my_database = None
my_tempdir = None
my_libdir = None


def default_database():
    """Get default database depending on what host we are on"""

    try:
        return os.environ["REMDB"]
    except KeyError:
        pass;
    hostn = os.uname().nodename
    if hostn == "lexi" or hostn == "nancy" or hostn == "foxy" :
        return "remfits"
    if hostn == "uhhpc":
        return "cluster"
    try:
        hostn.index("herts.ac.uk")
        return "cluster"
    except ValueError:
        pass
    return "remfits"


def get_tmpdir():
    """Select an appropriate temporty directory"""
    try:
        return  os.environ["REMTMP"]
    except KeyError:
        return  os.getcwd()


def get_libdir():
    """Select an appropriate library directory"""
    try:
        return os.environ["REMLIB"]
    except KeyError:
        ldir = os.path.expanduser("~/lib")
        if os.path.exists(ldir):
            return ldir
        return os.path.expanduser("~")


def parseargs(argp):
    """Parse arguments relevant to REM defaults"""
    argp.add_argument('--database', type=str, default=default_database(), help='Database to use')
    argp.add_argument('--tempdir', type=str, default=get_tmpdir(), help='Temp directory to unload files')
    argp.add_argument('--libdir', type=str, default=get_libdir(), help='REM library to use')


def getargs(resargs):
    """Get supplied arguments and apply"""
    global my_database, my_tempdir, my_libdir

    my_database = resargs['database']
    my_tempdir = resargs['tempdir']
    my_libdir = resargs['libdir']


def opendb():
    """Open database and return tuple dbase connection and cursor"""
    global my_database
    dbase = dbops.opendb(my_database)
    dbcurs = dbase.cursor()
    return (dbase, dbcurs)


def tempfile(name):
    """Get temporary file with given name as base name.
    If we haven't got my_tempdir set, assume we're chdired to temp directory
    to avoid confusing existing software"""
    global my_tempdir
    if my_tempdir is None:
        return name
    return os.path.join(my_tempdir, name)


def libfile(name):
    """Construct library file path using defaults or other setting"""
    global my_libdir
    if my_libdir is None:
        my_libdir = get_libdir()
    return os.path.join(my_libdir, name)
