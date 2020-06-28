# Arg parsing for selecting obs or daily flat/bias


class RemFieldError(Exception):
    """Throw this to indicate error in pair parse"""
    pass


def parseargs(argp):
    """"Set up arguments for range selection"""
    xtra = " value to restrict to as m:n"
    argp.add_argument('--minval', type=str, help='Minimum' + xtra)
    argp.add_argument('--maxval', type=str, help='Maximum' + xtra)
    argp.add_argument('--median', type=str, help='Median' + xtra)
    argp.add_argument('--mean', type=str, help='Meanv' + xtra)
    argp.add_argument('--std', type=str, help='Stde dev' + xtra)
    argp.add_argument('--skew', type=str, help='Skew' + xtra)
    argp.add_argument('--kurt', type=str, help='Kurtosis' + xtra)


def parsepair(resargs, name, fslist, colname):
    """Parse an argument pair of the form a:b with a and b optional and
    generate a field selection thing for database."""

    arg = resargs[name]
    if arg is None:
        return
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


def getargs(resargs, fslist):
    """Get and parse one of the arguments"""
    parsepair(resargs, "minval", fslist, "minv")
    parsepair(resargs, "maxval", fslist, "maxv")
    parsepair(resargs, "median", fslist, "median")
    parsepair(resargs, "mean", fslist, "mean")
    parsepair(resargs, "std", fslist, "std")
    parsepair(resargs, "skew", fslist, "skew")
    parsepair(resargs, "kurt", fslist, "kurt")
