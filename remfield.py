# Arg parsing for selecting obs or daily flat/bias

# import sys


class RemFieldError(Exception):
    """Throw this to indicate error in pair parse"""
    pass

# Table of argument names descriptions and database field names


Arg_names = (('minval', 'Minimum value', 'minv'),
            ('maxval', 'Maximum value', 'maxv'),
            ('median', 'Median', 'median'),
            ('mean', 'Mean', 'mean'),
            ('std', 'Standard deviation', 'std'),
            ('skew', 'Skewness', 'skew'),
            ('kurt', 'Kurtosis', 'kurt'))


def parseargs(argp, multstd=False):
    """"Set up arguments for range selection
    If multstd is given, also add options for selection of multiples of std deviation"""
    xtra = " value to restrict to as m:n"
    for argn, descr, dbf in Arg_names:
        argp.add_argument('--' + argn, type=str, help=descr + xtra)
    if multstd:
        xtra1 = 'Multiples of std dev of '
        xtra1a = 'Abs value of multiples of std dev of '
        xtra2 = ' value to restrict to as m:n'
        for argn, descr, dbf in Arg_names:
            argp.add_argument('--nstd_' + argn, type=str, help=xtra1 + descr + xtra2)
            argp.add_argument('--abs_nstd_' + argn, type=str, help=xtra1a + descr + xtra2)


def parsepair(resargs, name, fslist, colname):
    """Parse an argument pair of the form a:b with a and b optional and
    generate a field selection thing for database. Return True if we parsed something"""

    arg = resargs[name]
    if arg is None:
        return False
    # Bodge because it gets args starting with - wrong
    if len(arg) > 2 and arg[1] == '-':
        arg = arg[1:]
    bits = arg.split(':')
    if len(bits) != 2:
        raise RemFieldError("Cannot understand " + name + " arg expection m:n with either number opptional")
    lov, hiv = bits
    if len(lov) != 0:
        fslist.append(colname + ">=" + lov)
    if len(hiv) != 0:
        fslist.append(colname + "<=" + hiv)
    return True


def getargs(resargs, fslist):
    """Get and parse the standard arguments"""
    for argn, descr, dbf in Arg_names:
        parsepair(resargs, argn, fslist, dbf)


def get_extended_args(resargs, tab, prefix, fieldselect, needextra=False):
    """Build extended selection statement with prefix given and existing selection fields"""
    extrafields = 0
    mainsel = []
    noextra_mainsel = []
    innersel = ["filter as workfilt"]
    havingcl = []
    matchtab = ["filter=workfilt"]
    for argn, descr, dbf in Arg_names:
        mainsel.append(dbf)
        noextra_mainsel.append(dbf)
        mainsel.append("(" + dbf + "-work.mean_" + dbf + ")/work.std_" + dbf + " AS ns_" + dbf)
        mainsel.append("ABS(" + dbf + "-work.mean_" + dbf + ")/work.std_" + dbf + " AS absns_" + dbf)
        noextra_mainsel.append("0")
        noextra_mainsel.append("0")
        innersel.append("AVG(" + dbf + ") AS mean_" + dbf)
        innersel.append("STD(" + dbf + ") AS std_" + dbf)
        if parsepair(resargs, "nstd_" + argn, havingcl, "ns_" + dbf): extrafields += 1
        if parsepair(resargs, "abs_nstd_" + argn, havingcl, "absns_" + dbf): extrafields += 1
        matchtab.append("std_" + dbf + "!=0")

    resselstr = prefix
    if len(resselstr) != 0 and resselstr[-1] != ',':
        resselstr += ","
    # print("Extra fields", extrafields, file=sys.stderr)
    if needextra or extrafields > 0:
        resselstr += ",".join(mainsel) + " FROM " + tab
        resselstr += ",(SELECT " + ",".join(innersel)
        resselstr += " FROM " + tab + " WHERE " + " AND ".join(fieldselect)
        resselstr += " GROUP BY workfilt) AS work WHERE " + " AND ".join(matchtab + fieldselect)
        if len(havingcl) != 0:
            resselstr += " HAVING " + " AND ".join(havingcl)
    else:
        resselstr += ",".join(noextra_mainsel) + " FROM " + tab + " WHERE " + " AND ".join(fieldselect)
    return  resselstr
