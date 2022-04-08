"""Save search param settings"""

import xml.etree.ElementTree as ET
import xmlutil
import configfile

# These are the default values for the seqrch parameters

DEFAULT_SIGN = 1.5
DEFAULT_TOTSIGN = .75
DEFAULT_MAXSHIFT = 10
DEFAULT_DEFAPSIZE = 6
DEFAULT_MINAP = 3
DEFAULT_MAXAP = 20


class SearchParamErr(Exception):
    """Throw in case of errors"""


Field_names = dict(signif=(xmlutil.getfloat,
                             float,
                             DEFAULT_SIGN,
                             "Multiple of std devs above sky level to consider point significant"),
                    totsig=(xmlutil.getfloat,
                              float,
                              DEFAULT_TOTSIGN,
                              "Total nomber of std devs to consider a peak significant"),
                    maxshift=(xmlutil.getint,
                               int,
                               DEFAULT_MAXSHIFT,
                               "Max displacement from expected position to consider "),
                   defapsize=(xmlutil.getint,
                                int,
                                DEFAULT_DEFAPSIZE,
                                "Default aperture size if none given"),
                   minap=(xmlutil.getint,
                            int,
                            DEFAULT_MINAP,
                            "Minimum aperture size when optimising aperture"),
                   maxap=(xmlutil.getint,
                            int,
                            DEFAULT_MAXAP,
                            "Maximum aperture size when optimising aperture"))


class SearchParam:
    """Remember search params"""

    def __init__(self):
        self.signif = DEFAULT_SIGN
        self.totsig = DEFAULT_TOTSIGN
        self.maxshift = DEFAULT_MAXSHIFT
        self.defapsize = DEFAULT_DEFAPSIZE
        self.minap = DEFAULT_MINAP
        self.maxap = DEFAULT_MAXAP
        self.saveparams = False

    def load(self, node):
        """Load parameters from XML file"""
        self.saveparams = False
        for f, v in Field_names.items():
            dummy, dummy, defv, dummy = v
            setattr(self, f, defv)
        for child in node:
            tagn = child.tag
            try:
                setattr(self, tagn, Field_names[tagn][0](child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        for tagn in Field_names:
            xmlutil.savedata(doc, node, tagn, getattr(self, tagn))
        return  node

    def argparse(self, argp):
        """Initialise arg parser with search options"""
        for f, v in Field_names.items():
            dummy, typ, dummy, helpm = v
            argp.add_argument('--' + f, type=typ, default=getattr(self, f, 0), help=helpm)
        argp.add_argument('--search-save', action='store_true', help='Save new search parametrs file')

    def getargs(self, resargs):
        """Get search options"""

        for f in Field_names:
            setattr(self, f, resargs[f])
        self.saveparams = resargs['search-save']


def load(fname=None, mustexist=False):
    """Load search params from file"""
    if fname is None:
        fname = "searchparams"
    ret = SearchParam()
    try:
        dr = configfile.load(fname, "SEARCHPAR")
    except configfile.ConfigError as e:
        raise SearchParamErr(e.args[0])
    if dr is None:
        if mustexist:
            raise SearchParamErr("Cannot open " + fname)
        return ret
    for child in dr[1]:
        if child.tag == "searchp":
            ret.load(child)
    return ret


def save(rg, fname=None):
    """Save search params to file"""
    if fname is None:
        fname = "searchparams"
    doc, root = configfile.init_save("SEARCHPAR")
    rg.save(doc, root, "searchp")
    try:
        configfile.complete_save(doc, fname)
    except configfile.ConfigError as e:
        raise SearchParamErr(e.args[0])
