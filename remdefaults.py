"""Default settings for REM programs"""

import datetime
import os
import os.path
import numpy as np
import dbops
import miscutils


class RemDefError(Exception):
    """Throw if we hit some kind of error"""


my_database = None
my_tempdir = None
my_libdir = None
my_inlib = True

# Dates on which geometry got changed in ascending order

regeom_dates = (datetime.date(2015, 7, 27),
                datetime.date(2019, 3, 27))

# Geometry first prior to first date, then after each date
# For each filter a tuple startx, starty, columns, rows

regeom_config = (dict(z=(138, 42, 944, 960), r=(1138, 48, 910, 958), i=(62, 1112, 954, 936), g=(1124, 1082, 924, 928)),
                 dict(z=(132, 22, 906, 956), r=(1148, 18, 900, 954), i=(94, 1112, 960, 936), g=(1170, 1072, 878, 932)),
                 dict(z=(80, 0, 914, 960), r=(1140, 2, 908, 954), i=(80, 1104, 912, 936), g=(1148, 1054, 900, 952)))


def get_geom(datet, filt):
    """Get geometry as tuple startx, starty, columns, rows corresponding to date and filter"""

    if isinstance(datet, datetime.datetime):
        datet = datet.date()
    p = len(regeom_dates)
    for pd in reversed(regeom_dates):
        if datet >= pd:
            try:
                return regeom_config[p][filt]
            except KeyError:
                return (0, 0, 512, 512)
        p -= 1
    try:
        return regeom_config[0][filt]
    except KeyError:
        return (0, 0, 512, 512)


def default_database():
    """Get default database depending on what host we are on"""

    try:
        return os.environ["REMDB"]
    except KeyError:
        pass
    hostn = os.uname().nodename
    if hostn in ("lexi", "nancy", "foxy"):
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


def parseargs(argp, inlib=True, libdir=True, tempdir=True, database=True):
    """Parse arguments relevant to REM defaults"""
    if database:
        argp.add_argument('--database', type=str, default=default_database(), help='Database to use')
    if tempdir:
        argp.add_argument('--tempdir', type=str, default=get_tmpdir(), help='Temp directory to unload files')
    if libdir:
        argp.add_argument('--libdir', type=str, default=get_libdir(), help='REM library to use')
        act = 'store_true'
        if inlib:
            act = 'store_false'
        argp.add_argument('--inlib', action=act, help='Load and store in library rather than CWD by default')


def getargs(resargs):
    """Get supplied arguments and apply"""
    global my_database, my_tempdir, my_libdir, my_inlib
    try:
        my_database = resargs['database']
    except KeyError:
        pass
    try:
        my_tempdir = resargs['tempdir']
    except KeyError:
        pass
    try:
        my_libdir = resargs['libdir']
        my_inlib = resargs['inlib']
    except KeyError:
        pass


def opendb(waitlock=False):
    """Open database and return tuple dbase connection and cursor"""
    global my_database
    if my_database is None:
        my_database = default_database()
    dbase = dbops.opendb(my_database)
    dbcurs = dbase.cursor()
    if waitlock:
        dbcurs = dbops.DBops_cursor(dbcurs)
    return (dbase, dbcurs)


def tempfile(name):
    """Get temporary file with given name as base name.
    If we haven't got my_tempdir set, assume we're chdired to temp directory
    to avoid confusing existing software"""
    global my_tempdir
    if my_tempdir is None:
        return name
    return os.path.join(my_tempdir, name)


def libfile(name, insist=False):
    """Construct library file path using defaults or other setting"""
    global my_libdir, my_inlib
    if not (my_inlib or insist):
        return name
    if my_libdir is None:
        my_libdir = get_libdir()
    return os.path.join(my_libdir, name)

def rem_replacesuffix(name, newsuffix):
    """Replace suffix used by remfits with appropriate suffix"""
    return  miscutils.replacesuffix(name, newsuffix, ("fits.gz",
                                                      "findres",
                                                      "objloc",
                                                      "edits",
                                                      "tally",
                                                      "fitsids",
                                                      "meanstd",
                                                      "badpix",
                                                      "counts",
                                                      "stdarray"))

def tally_file(name):
    """Get the location of a tally file of given name"""
    return libfile(rem_replacesuffix(name, "tally"))

def fitsid_file(name):
    """Get the location of a fitsids file of given name"""
    return libfile(rem_replacesuffix(name, "fitsids"))

def meanstd_file(name):
    """Get the location of a mean/std file of given name"""
    return libfile(rem_replacesuffix(name, "meanstd"))

def bad_pixmask(name):
    """Get the location of a bad pixel mask of given name"""
    return libfile(rem_replacesuffix(name, "badpix"))

def count_file(name):
    """Get the location of a count-type file (used for counting neg pixels)"""
    return libfile(rem_replacesuffix(name, "counts"))

def objloc_file(name):
    """Get the location of an object location file"""
    return rem_replacesuffix(name, "objloc")

def findres_file(name):
    """Get the location of a find results file"""
    return rem_replacesuffix(name, "findres")

def edits_file(name):
    """Get the location of an edits file"""
    return rem_replacesuffix(name, "edits")

def apopt_file(name):
    """Get the location of an aperture opt file"""
    return rem_replacesuffix(name, "apopt")

def stdarray_file(name):
    """Get the location of an aperture opt file"""
    return libfile(rem_replacesuffix(name, "stdarray"))

# def skymap_file(starname, dat):
#     """Generate sky map file using base name and date"""
#     return libfile("skymaps/{:s}-{:%Y-%m-%d}.skymap".format(starname, dat), insist=True)
#
#
# def skymap_glob(starname):
#     """Run glob on skymaps for given name"""
#     return  glob.iglob(libfile("skymaps/" + starname + "-*.skymap", insist=True))
#
#
# def nearest_skymap_file(starname, dat):
#     """Get nearest skymap file in time.
#     Return tuple of name and date"""
#     sklist = []
#     dayslist = []
#     fdatelist = []
#     if isinstance(dat, datetime.datetime):
#         dat = dat.date()
#     for sk in skymap_glob(starname):
#         mtch = smmatch.match(sk)
#         if mtch is None:
#             continue
#         try:
#             fdate = datetime.date(*map(int, mtch.groups()))
#             sdays = abs(dat - fdate)
#         except ValueError:
#             continue
#         dayslist.append(sdays)
#         sklist.append(sk)
#         fdatelist.append(fdate)
#     if len(sklist) == 0:
#         return  None
#     minind = dayslist.index(min(dayslist))
#     return (sklist[minind], fdatelist[minind])


def load_bad_pixmask(name):
    """Load bad pixel mask file"""

    badpixf = bad_pixmask(name)
    try:
        badpixmask = np.load(badpixf)
    except FileNotFoundError:
        raise RemDefError("Bad pixel file " + badpixf + " does not exist")
    except PermissionError:
        raise RemDefError("No open permission on file " + badpixf)
    except ValueError:
        raise RemDefError("Bad pixel file " + badpixf + " did not load")
    if badpixmask.dtype != np.bool:
        raise RemDefError("Bad pixel file " + badpixf + " not boolean")
    if badpixmask.shape != (2048, 2048):
        raise RemDefError("Bad pixel file " + badpixf + " incorrect shape " + str(badpixmask.shape) + " should be 2048x2048")
    return  badpixmask
